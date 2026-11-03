"""Send one command to a gateway over MQTT and print the acks. For bench testing.

python tools/send_command.py motor_start --site plant-a --machine press-01 [--ttl 10] [--host 127.0.0.1]
"""
from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timedelta, timezone

import paho.mqtt.client as mqtt


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command")
    ap.add_argument("--site", default="plant-a")
    ap.add_argument("--machine", default="press-01")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--ttl", type=float, default=10, help="seconds until the command expires; negative sends an already-expired one")
    ap.add_argument("--by", default="bench-test")
    ap.add_argument("--wait", type=float, default=5, help="seconds to wait for acks")
    args = ap.parse_args()

    base = f"factory/{args.site}/{args.machine}"
    now = datetime.now(timezone.utc)
    cmd = {
        "cmd_id": str(uuid.uuid4()),
        "command": args.command,
        "params": {},
        "issued_by": args.by,
        "issued_at": iso(now),
        "expires_at": iso(now + timedelta(seconds=args.ttl)),
    }

    def on_message(client, userdata, msg):
        ack = json.loads(msg.payload)
        if ack.get("cmd_id") == cmd["cmd_id"]:
            print("ack:", json.dumps(ack))

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"bench-{uuid.uuid4().hex[:8]}")
    c.on_message = on_message
    c.connect(args.host, args.port)
    c.subscribe(f"{base}/cmd/ack", qos=1)
    c.loop_start()
    time.sleep(0.3)
    print("sent:", json.dumps(cmd))
    c.publish(f"{base}/cmd", json.dumps(cmd), qos=1).wait_for_publish(3)
    time.sleep(args.wait)
    c.loop_stop()
    c.disconnect()


if __name__ == "__main__":
    main()
