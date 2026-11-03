"""Load and validate gateway.yaml."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REGISTER_TYPES = {"holding", "input"}
BIT_TYPES = {"coil", "discrete"}
FORMATS = {"uint16": 1, "int16": 1, "uint32": 2, "int32": 2, "float32": 2}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Tag:
    name: str
    type: str
    address: int
    format: str = "uint16"
    scale: float | None = None
    enum: dict[int, str] | None = None

    @property
    def words(self) -> int:
        return FORMATS[self.format] if self.type in REGISTER_TYPES else 1


@dataclass(frozen=True)
class Command:
    name: str
    type: str
    address: int
    pulse_ms: int | None = None
    value: int | None = None


@dataclass
class Config:
    site: str
    machine_id: str
    plc: dict[str, Any]
    mqtt: dict[str, Any]
    tags: list[Tag]
    control_enabled: bool = False
    max_ttl_s: float = 30
    require: dict[str, Any] | None = None
    heartbeat: dict[str, Any] = field(default_factory=dict)
    commands: dict[str, Command] = field(default_factory=dict)

    def topic(self, leaf: str) -> str:
        return f"factory/{self.site}/{self.machine_id}/{leaf}"


def _tag(name: str, spec: dict[str, Any]) -> Tag:
    t = spec.get("type")
    if t not in REGISTER_TYPES | BIT_TYPES:
        raise ConfigError(f"read.{name}: type must be coil, discrete, holding or input")
    fmt = spec.get("format", "uint16")
    if fmt not in FORMATS:
        raise ConfigError(f"read.{name}: unknown format {fmt!r}")
    if t in BIT_TYPES and fmt != "uint16":
        raise ConfigError(f"read.{name}: format only applies to registers")
    enum = spec.get("enum")
    return Tag(
        name=name,
        type=t,
        address=int(spec["address"]),
        format=fmt,
        scale=spec.get("scale"),
        enum={int(k): str(v) for k, v in enum.items()} if enum else None,
    )


def _command(name: str, spec: dict[str, Any]) -> Command:
    t = spec.get("type")
    if t == "coil":
        return Command(name, t, int(spec["address"]), pulse_ms=spec.get("pulse_ms"), value=spec.get("value"))
    if t == "holding":
        if "value" not in spec:
            raise ConfigError(f"control.commands.{name}: holding commands need a fixed value")
        return Command(name, t, int(spec["address"]), value=int(spec["value"]))
    raise ConfigError(f"control.commands.{name}: type must be coil or holding")


def load(path: str | Path) -> Config:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    try:
        tags = [_tag(n, s) for n, s in (raw.get("read") or {}).items()]
        control = raw.get("control") or {}
        cfg = Config(
            site=str(raw["site"]),
            machine_id=str(raw["machine_id"]),
            plc=raw["plc"],
            mqtt=raw["mqtt"],
            tags=tags,
            control_enabled=bool(control.get("enabled", False)),
            max_ttl_s=float(control.get("max_ttl_s", 30)),
            require=control.get("require"),
            heartbeat=control.get("heartbeat") or {},
            commands={n: _command(n, s) for n, s in (control.get("commands") or {}).items()},
        )
    except KeyError as e:
        raise ConfigError(f"missing required key {e}") from None
    if not cfg.tags:
        raise ConfigError("read: at least one tag is required")
    if cfg.require and cfg.require.get("tag") not in {t.name for t in cfg.tags}:
        raise ConfigError("control.require.tag must name a tag under read")
    if cfg.plc.get("protocol", "modbus_tcp") != "modbus_tcp":
        raise ConfigError("plc.protocol: only modbus_tcp is implemented")
    return cfg
