"""Main loop: poll the PLC, publish telemetry, process queued commands."""
from __future__ import annotations

import json
import logging
import queue
import signal
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt

from . import commands
from .config import Config
from .plc import Plc, PlcError

log = logging.getLogger(__name__)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class Gateway:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.plc = Plc(cfg)
        self.seq = 0
        self.latest: dict[str, Any] | None = None
        self.cmd_queue: queue.Queue[bytes] = queue.Queue(maxsize=100)
        self.seen = commands.SeenIds()
        self.buffer: deque[tuple[str, str, bool]] = deque(maxlen=int(cfg.mqtt.get("offline_buffer", 10000)))
        self.connected = threading.Event()
        self.stop = threading.Event()
        self.hb_value = 0
        self.hb_next = 0.0
        self.mqtt = self._make_client()

    # ---------- MQTT ----------
    def _make_client(self) -> mqtt.Client:
        m = self.cfg.mqtt
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=m.get("client_id") or self.cfg.machine_id)
        if m.get("username"):
            c.username_pw_set(m["username"], m.get("password"))
        tls = m.get("tls") or {}
        if tls.get("enabled"):
            c.tls_set(ca_certs=tls.get("ca_file"), certfile=tls.get("cert_file"), keyfile=tls.get("key_file"))
        c.will_set(self.cfg.topic("status"), json.dumps({"state": "offline"}), qos=1, retain=True)
        c.reconnect_delay_set(min_delay=1, max_delay=60)
        c.on_connect = self._on_connect
        c.on_disconnect = self._on_disconnect
        c.on_message = self._on_message
        return c

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("MQTT connect refused: %s", reason_code)
            return
        log.info("MQTT connected")
        client.publish(self.cfg.topic("status"), json.dumps({"state": "online", "ts": utc_now()}), qos=1, retain=True)
        client.subscribe(self.cfg.topic("cmd"), qos=1)
        self.connected.set()

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.connected.clear()
        log.warning("MQTT disconnected: %s", reason_code)

    def _on_message(self, client, userdata, msg):
        try:
            self.cmd_queue.put_nowait(msg.payload)
        except queue.Full:
            log.error("command queue full, dropping message")

    def publish(self, leaf: str, payload: dict[str, Any], retain: bool = False) -> None:
        topic, body = self.cfg.topic(leaf), json.dumps(payload, separators=(",", ":"))
        if self.connected.is_set():
            self._flush()
            info = self.mqtt.publish(topic, body, qos=1, retain=retain)
            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                return
        if leaf == "telemetry":
            self.buffer.append((topic, body, retain))   # only telemetry is worth replaying

    def _flush(self) -> None:
        while self.buffer and self.connected.is_set():
            topic, body, retain = self.buffer.popleft()
            self.mqtt.publish(topic, body, qos=1, retain=retain)

    # ---------- commands ----------
    def ack(self, cmd_id: str | None, status: str, reason: str | None = None) -> None:
        payload = {"cmd_id": cmd_id, "status": status, "ts": utc_now()}
        if reason:
            payload["reason"] = reason
        log.info("ack %s %s %s", cmd_id, status, reason or "")
        self.publish("cmd/ack", payload)

    def process_commands(self) -> None:
        while True:
            try:
                payload = self.cmd_queue.get_nowait()
            except queue.Empty:
                return
            v = commands.validate(payload, self.cfg, self.seen, self.latest)
            self.ack(v.cmd_id, v.status, v.reason)
            if v.status != "accepted":
                continue
            try:
                self.plc.execute(v.command)
                self.ack(v.cmd_id, "executed")
            except PlcError as e:
                self.ack(v.cmd_id, "rejected", f"PLC write failed: {e}")

    # ---------- loop ----------
    def heartbeat(self) -> None:
        hb = self.cfg.heartbeat
        if not (self.cfg.control_enabled and hb.get("enabled")) or time.monotonic() < self.hb_next:
            return
        self.hb_next = time.monotonic() + float(hb.get("interval_s", 2))
        self.hb_value = (self.hb_value + 1) & 0xFFFF
        try:
            self.plc.write_heartbeat(int(hb["address"]), self.hb_value)
        except PlcError as e:
            log.warning("heartbeat write failed: %s", e)

    def poll_once(self) -> None:
        try:
            values = self.plc.read_all()
        except PlcError as e:
            self.latest = None
            log.warning("PLC read failed: %s", e)
            self.publish("state", {"ts": utc_now(), "machine_id": self.cfg.machine_id, "plc": "unreachable"}, retain=True)
            return
        self.latest = values
        self.seq += 1
        msg = {"ts": utc_now(), "machine_id": self.cfg.machine_id, "seq": self.seq, "metrics": values}
        self.publish("telemetry", msg)
        self.publish("state", {**msg, "plc": "ok"}, retain=True)

    def run(self) -> None:
        m = self.cfg.mqtt
        self.mqtt.connect_async(m["host"], int(m.get("port", 1883)), keepalive=int(m.get("keepalive_s", 30)))
        self.mqtt.loop_start()
        interval = float(self.cfg.plc.get("poll_interval_s", 1.0))
        log.info("gateway %s started, control %s", self.cfg.machine_id, "ENABLED" if self.cfg.control_enabled else "disabled")
        try:
            while not self.stop.is_set():
                started = time.monotonic()
                self.poll_once()
                self.process_commands()
                self.heartbeat()
                # Wake early for commands instead of waiting out the whole interval.
                while not self.stop.is_set() and time.monotonic() - started < interval:
                    if not self.cmd_queue.empty():
                        self.process_commands()
                    time.sleep(0.05)
        finally:
            if self.connected.is_set():
                self.mqtt.publish(self.cfg.topic("status"), json.dumps({"state": "offline", "ts": utc_now()}), qos=1, retain=True).wait_for_publish(2)
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
            self.plc.close()
            log.info("gateway stopped")

    def install_signal_handlers(self) -> None:
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: self.stop.set())
