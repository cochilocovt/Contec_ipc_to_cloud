"""Ingest service: MQTT -> TimescaleDB.

Subscribes to every gateway's telemetry, status, commands and acks, and writes them
to the tables in db/init/01-schema.sql. Database writes happen on the main thread;
the MQTT thread only queues messages, so a slow or restarting database never
blocks the broker connection.
"""
from __future__ import annotations

import json
import logging
import os
import queue
import signal
import threading
import time
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt
import psycopg
from psycopg.types.json import Jsonb

log = logging.getLogger("ingest")
SUBSCRIPTIONS = ["factory/+/+/telemetry", "factory/+/+/status", "factory/+/+/cmd", "factory/+/+/cmd/ack"]


def parse_ts(s: Any) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else None


def split_topic(topic: str) -> tuple[str, str, str] | None:
    parts = topic.split("/")
    if len(parts) < 4 or parts[0] != "factory":
        return None
    return parts[1], parts[2], "/".join(parts[3:])


def telemetry_rows(machine_id: str, msg: dict[str, Any]) -> list[tuple]:
    ts = parse_ts(msg.get("ts"))
    metrics = msg.get("metrics")
    if ts is None or not isinstance(metrics, dict):
        raise ValueError("telemetry needs ts with offset and a metrics object")
    seq = msg.get("seq")
    rows = []
    for name, v in metrics.items():
        if isinstance(v, bool):
            rows.append((ts, machine_id, name, 1.0 if v else 0.0, None, seq))
        elif isinstance(v, (int, float)):
            rows.append((ts, machine_id, name, float(v), None, seq))
        elif v is None:
            continue
        else:
            rows.append((ts, machine_id, name, None, str(v), seq))
    return rows


class Ingest:
    def __init__(self, mqtt_host: str, mqtt_port: int, dsn: str):
        self.dsn = dsn
        self.q: queue.Queue[tuple[str, bytes]] = queue.Queue(maxsize=50_000)
        self.stop = threading.Event()
        self.conn: psycopg.Connection | None = None
        # Keep the subscription while offline so gateway replay cannot beat our reconnect.
        self.mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ingest", clean_session=False)
        self.mqtt.on_connect = self._on_connect
        self.mqtt.on_message = self._on_message
        self.mqtt.reconnect_delay_set(1, 30)
        self.mqtt_host, self.mqtt_port = mqtt_host, mqtt_port

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("MQTT connect refused: %s", reason_code)
            return
        for t in SUBSCRIPTIONS:
            client.subscribe(t, qos=1)
        log.info("MQTT connected, subscribed to %d topics", len(SUBSCRIPTIONS))

    def _on_message(self, client, userdata, msg):
        try:
            self.q.put_nowait((msg.topic, msg.payload))
        except queue.Full:
            log.error("queue full, dropping %s", msg.topic)

    # ---------- database ----------
    def db(self) -> psycopg.Connection:
        while self.conn is None or self.conn.closed:
            try:
                self.conn = psycopg.connect(self.dsn, autocommit=True)
                log.info("database connected")
            except psycopg.OperationalError as e:
                log.warning("database unavailable (%s), retrying in 3s", e)
                if self.stop.wait(3):
                    raise SystemExit(0)
        return self.conn

    def handle(self, topic: str, payload: bytes) -> None:
        parsed = split_topic(topic)
        if not parsed:
            return
        site, machine_id, leaf = parsed
        try:
            msg = json.loads(payload)
            if not isinstance(msg, dict):
                raise ValueError("not a JSON object")
        except ValueError as e:
            log.warning("bad JSON on %s: %s", topic, e)
            return

        cur = self.db().cursor()
        if leaf == "telemetry":
            try:
                rows = telemetry_rows(machine_id, msg)
            except ValueError as e:
                log.warning("%s: %s", topic, e)
                return
            cur.executemany(
                "INSERT INTO telemetry (ts, machine_id, metric, value, value_text, seq) VALUES (%s,%s,%s,%s,%s,%s)", rows)

        elif leaf == "status":
            cur.execute(
                """INSERT INTO gateway_status (machine_id, site, state, ts, received_at) VALUES (%s,%s,%s,%s,now())
                   ON CONFLICT (machine_id) DO UPDATE SET site=EXCLUDED.site, state=EXCLUDED.state,
                   ts=EXCLUDED.ts, received_at=now()""",
                (machine_id, site, str(msg.get("state", "unknown")), parse_ts(msg.get("ts"))))

        elif leaf == "cmd":
            issued, expires = parse_ts(msg.get("issued_at")), parse_ts(msg.get("expires_at"))
            if not (isinstance(msg.get("cmd_id"), str) and isinstance(msg.get("command"), str) and issued and expires):
                log.warning("command on %s missing fields; not recorded (the gateway will reject it)", topic)
                return
            cur.execute(
                """INSERT INTO commands (cmd_id, site, machine_id, command, params, issued_by, issued_at, expires_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (cmd_id) DO NOTHING""",
                (msg["cmd_id"], site, machine_id, msg["command"], Jsonb(msg.get("params") or {}),
                 str(msg.get("issued_by") or "unknown"), issued, expires))

        elif leaf == "cmd/ack":
            cmd_id, status = msg.get("cmd_id"), str(msg.get("status", "unknown"))
            cur.execute(
                "INSERT INTO command_events (cmd_id, machine_id, status, reason, ts) VALUES (%s,%s,%s,%s,%s)",
                (cmd_id, machine_id, status, msg.get("reason"), parse_ts(msg.get("ts"))))
            if isinstance(cmd_id, str):
                cur.execute("UPDATE commands SET status=%s, reason=%s, updated_at=now() WHERE cmd_id=%s",
                            (status, msg.get("reason"), cmd_id))

    def run(self) -> None:
        self.db()
        self.mqtt.connect_async(self.mqtt_host, self.mqtt_port, keepalive=30)
        self.mqtt.loop_start()
        written = 0
        last_report = time.monotonic()
        try:
            while not self.stop.is_set():
                try:
                    topic, payload = self.q.get(timeout=0.5)
                except queue.Empty:
                    continue
                for attempt in range(3):
                    try:
                        self.handle(topic, payload)
                        written += 1
                        break
                    except psycopg.OperationalError as e:
                        log.warning("database error (%s), reconnecting", e)
                        self.conn = None
                    except psycopg.Error as e:
                        log.error("could not store %s: %s", topic, e)
                        break
                if time.monotonic() - last_report > 60:
                    log.info("stored %d messages in the last minute, %d queued", written, self.q.qsize())
                    written, last_report = 0, time.monotonic()
        finally:
            self.mqtt.loop_stop()
            if self.conn:
                self.conn.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = Ingest(os.environ.get("MQTT_HOST", "localhost"), int(os.environ.get("MQTT_PORT", "1883")),
                 os.environ["DATABASE_URL"])
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: app.stop.set())
    app.run()


if __name__ == "__main__":
    main()
