"""Simulated PLC for bench testing without the real machine.

Serves Modbus TCP with the same map as gateway/config/gateway.example.yaml:

  coil 0      motor_running        (read)
  coil 10     motor_start pulse    (write, acted on at the rising edge)
  coil 11     motor_stop pulse     (write)
  hr 100      motor_speed_rpm
  hr 101      motor_current_a x10
  hr 102      spindle_temp_c x10
  hr 103      mode  0=LOCAL 1=REMOTE
  hr 104-105  part_count uint32, big-endian words
  hr 106      fault_code           (9 = remote heartbeat lost)
  hr 110      heartbeat            (written by the gateway)

Like a real PLC, it ignores start commands unless mode is REMOTE, and it stops
the motor when the gateway heartbeat goes stale (if --heartbeat-timeout is set).

Run:  python tools/sim_plc.py --port 5020 [--mode local] [--heartbeat-timeout 6]
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import math
import random
import time

from pymodbus.datastore import ModbusDeviceContext, ModbusSequentialDataBlock, ModbusServerContext
from pymodbus.server import StartAsyncTcpServer

COILS, HOLDING = 1, 3   # function codes used to address the data blocks
log = logging.getLogger("sim_plc")


def build_context() -> ModbusServerContext:
    device = ModbusDeviceContext(
        di=ModbusSequentialDataBlock(0, [0] * 200),
        co=ModbusSequentialDataBlock(0, [0] * 200),
        ir=ModbusSequentialDataBlock(0, [0] * 200),
        hr=ModbusSequentialDataBlock(0, [0] * 200),
    )
    return ModbusServerContext(devices=device, single=True)


async def machine(ctx: ModbusServerContext, mode: str, hb_timeout: float | None) -> None:
    dev = ctx[0]
    get = lambda fc, a, n=1: dev.getValues(fc, a, n)  # noqa: E731
    put = lambda fc, a, v: dev.setValues(fc, a, v)    # noqa: E731
    put(HOLDING, 103, [1 if mode == "remote" else 0])

    running, rpm, temp, parts = False, 0.0, 25.0, 0
    prev_start = prev_stop = False
    last_hb, hb_seen_at = None, time.monotonic()
    t0 = time.monotonic()

    while True:
        start, stop = (bool(x) for x in get(COILS, 10, 2))
        remote = get(HOLDING, 103)[0] == 1

        hb = get(HOLDING, 110)[0]
        if hb != last_hb:
            last_hb, hb_seen_at = hb, time.monotonic()
        hb_stale = hb_timeout is not None and time.monotonic() - hb_seen_at > hb_timeout

        if start and not prev_start:
            if remote and not hb_stale:
                running = True
                put(HOLDING, 106, [0])
                log.info("START accepted")
            else:
                log.info("START ignored (%s)", "LOCAL mode" if not remote else "heartbeat stale")
        if stop and not prev_stop:
            running = False
            log.info("STOP")
        if running and remote and hb_stale:
            running = False
            put(HOLDING, 106, [9])
            log.warning("heartbeat lost: motor stopped, fault 9")
        prev_start, prev_stop = start, stop

        target = 1450.0 if running else 0.0
        rpm += (target - rpm) * 0.15
        temp += ((60.0 if running else 25.0) - temp) * 0.01
        if running and random.random() < 0.05:
            parts += 1
        wobble = 1 + 0.02 * math.sin(time.monotonic() - t0)
        current = (12.4 * wobble) if running else 0.0

        put(COILS, 0, [running])
        put(HOLDING, 100, [int(rpm)])
        put(HOLDING, 101, [int(current * 10)])
        put(HOLDING, 102, [int(temp * 10)])
        put(HOLDING, 104, [(parts >> 16) & 0xFFFF, parts & 0xFFFF])
        await asyncio.sleep(0.1)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5020)
    ap.add_argument("--mode", choices=["local", "remote"], default="remote")
    ap.add_argument("--heartbeat-timeout", type=float, default=None, help="seconds; omit to ignore the heartbeat")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    logging.getLogger("pymodbus").setLevel(logging.WARNING)

    ctx = build_context()
    log.info("simulated PLC on %s:%d, mode %s", args.host, args.port, args.mode.upper())
    await asyncio.gather(
        StartAsyncTcpServer(context=ctx, address=(args.host, args.port)),
        machine(ctx, args.mode, args.heartbeat_timeout),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
