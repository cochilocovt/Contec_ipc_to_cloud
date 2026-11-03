"""Command validation: allowlist, expiry, dedupe and the courtesy mode check.

Pure functions and a small dedupe cache, so the rules are easy to unit test.
The PLC remains the authority on whether a command actually runs.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import Command, Config

MAX_CMD_ID = 64


@dataclass
class Verdict:
    cmd_id: str | None
    status: str                      # accepted | rejected | expired
    reason: str | None = None
    command: Command | None = None


def _parse_time(s: Any) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else None   # naive timestamps are rejected: everything is UTC with an offset


class SeenIds:
    """Remembers recent cmd_ids so a redelivered QoS 1 message runs at most once."""

    def __init__(self, size: int = 1000):
        self.size = size
        self._ids: OrderedDict[str, None] = OrderedDict()

    def add(self, cmd_id: str) -> bool:
        """Returns False if the id was already seen."""
        if cmd_id in self._ids:
            return False
        self._ids[cmd_id] = None
        if len(self._ids) > self.size:
            self._ids.popitem(last=False)
        return True


def validate(payload: bytes | str, cfg: Config, seen: SeenIds, latest: dict[str, Any] | None,
             now: datetime | None = None) -> Verdict:
    now = now or datetime.now(timezone.utc)
    try:
        msg = json.loads(payload)
        if not isinstance(msg, dict):
            raise ValueError
    except (ValueError, TypeError):
        return Verdict(None, "rejected", "payload is not a JSON object")

    cmd_id = msg.get("cmd_id")
    if not isinstance(cmd_id, str) or not cmd_id or len(cmd_id) > MAX_CMD_ID:
        return Verdict(None, "rejected", "cmd_id missing or invalid")

    if not seen.add(cmd_id):
        return Verdict(cmd_id, "rejected", "duplicate cmd_id")

    if not cfg.control_enabled:
        return Verdict(cmd_id, "rejected", "control is disabled on this gateway")

    name = msg.get("command")
    cmd = cfg.commands.get(name) if isinstance(name, str) else None
    if cmd is None:
        return Verdict(cmd_id, "rejected", f"command not allowed: {name!r}")

    expires = _parse_time(msg.get("expires_at"))
    if expires is None:
        return Verdict(cmd_id, "rejected", "expires_at missing or not an ISO 8601 time with offset")
    if expires <= now:
        return Verdict(cmd_id, "expired", "expires_at is in the past")
    if (expires - now).total_seconds() > cfg.max_ttl_s:
        return Verdict(cmd_id, "rejected", f"expires_at is more than {cfg.max_ttl_s:g}s away")

    if cfg.require:
        if latest is None:
            return Verdict(cmd_id, "rejected", "no recent reading from the PLC")
        actual = latest.get(cfg.require["tag"])
        if actual != cfg.require["equals"]:
            return Verdict(cmd_id, "rejected", f"machine in {actual} mode")

    return Verdict(cmd_id, "accepted", command=cmd)
