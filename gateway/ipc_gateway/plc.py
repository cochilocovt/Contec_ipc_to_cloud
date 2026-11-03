"""Modbus TCP access to the PLC. Reads tags and performs allowlisted writes."""
from __future__ import annotations

import logging
import struct
import time
from typing import Any

from pymodbus.client import ModbusTcpClient

from .config import Command, Config, Tag

log = logging.getLogger(__name__)


class PlcError(RuntimeError):
    pass


def decode(tag: Tag, raw: list[int] | list[bool]) -> Any:
    """Turn raw Modbus values into the published value for one tag."""
    if tag.type in ("coil", "discrete"):
        return bool(raw[0])
    words = [int(w) & 0xFFFF for w in raw[: tag.words]]
    packed = struct.pack(f">{len(words)}H", *words)
    value: float | int = {
        "uint16": lambda: words[0],
        "int16": lambda: struct.unpack(">h", packed)[0],
        "uint32": lambda: struct.unpack(">I", packed)[0],
        "int32": lambda: struct.unpack(">i", packed)[0],
        "float32": lambda: struct.unpack(">f", packed)[0],
    }[tag.format]()
    if tag.enum is not None:
        return tag.enum.get(int(value), f"UNKNOWN({int(value)})")
    if tag.scale is not None:
        return round(value * tag.scale, 6)
    return value


class Plc:
    def __init__(self, cfg: Config):
        p = cfg.plc
        self.unit = int(p.get("unit_id", 1))
        self.client = ModbusTcpClient(p["host"], port=int(p.get("port", 502)), timeout=float(p.get("timeout_s", 2)))
        self.tags = cfg.tags

    def connect(self) -> bool:
        return bool(self.client.connect())

    def close(self) -> None:
        self.client.close()

    def _check(self, rr: Any, what: str) -> Any:
        if rr is None or rr.isError():
            raise PlcError(f"{what} failed: {rr}")
        return rr

    def read_all(self) -> dict[str, Any]:
        """Read every configured tag. One request per tag keeps the code simple; batch later if needed."""
        if not self.client.connected and not self.connect():
            raise PlcError("cannot connect to PLC")
        out: dict[str, Any] = {}
        for t in self.tags:
            try:
                if t.type == "coil":
                    rr = self._check(self.client.read_coils(t.address, count=1, device_id=self.unit), t.name)
                    raw = rr.bits
                elif t.type == "discrete":
                    rr = self._check(self.client.read_discrete_inputs(t.address, count=1, device_id=self.unit), t.name)
                    raw = rr.bits
                elif t.type == "holding":
                    rr = self._check(self.client.read_holding_registers(t.address, count=t.words, device_id=self.unit), t.name)
                    raw = rr.registers
                else:
                    rr = self._check(self.client.read_input_registers(t.address, count=t.words, device_id=self.unit), t.name)
                    raw = rr.registers
            except PlcError:
                raise
            except Exception as e:  # connection drops surface as pymodbus exceptions
                self.client.close()
                raise PlcError(f"{t.name}: {e}") from e
            out[t.name] = decode(t, raw)
        return out

    def execute(self, cmd: Command) -> None:
        """Perform one allowlisted write. Pulses reset the coil even if the sleep is interrupted."""
        if not self.client.connected and not self.connect():
            raise PlcError("cannot connect to PLC")
        if cmd.type == "coil":
            if cmd.pulse_ms:
                self._check(self.client.write_coil(cmd.address, True, device_id=self.unit), cmd.name)
                try:
                    time.sleep(cmd.pulse_ms / 1000)
                finally:
                    self._check(self.client.write_coil(cmd.address, False, device_id=self.unit), cmd.name)
            else:
                self._check(self.client.write_coil(cmd.address, bool(cmd.value), device_id=self.unit), cmd.name)
        else:
            self._check(self.client.write_register(cmd.address, int(cmd.value), device_id=self.unit), cmd.name)
        log.info("executed %s", cmd.name)

    def write_heartbeat(self, address: int, value: int) -> None:
        self._check(self.client.write_register(address, value & 0xFFFF, device_id=self.unit), "heartbeat")
