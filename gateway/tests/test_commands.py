import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ipc_gateway import commands
from ipc_gateway.config import load

EXAMPLE = Path(__file__).resolve().parents[1] / "config" / "gateway.example.yaml"
NOW = datetime(2026, 11, 3, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def cfg():
    c = load(EXAMPLE)
    c.control_enabled = True
    return c


def msg(**over):
    m = {"cmd_id": "c1", "command": "motor_start", "issued_by": "t",
         "issued_at": "2026-11-03T10:00:00Z", "expires_at": "2026-11-03T10:00:10Z"}
    m.update(over)
    return json.dumps(m)


REMOTE = {"mode": "REMOTE"}


def run(cfg, payload, latest=REMOTE, seen=None):
    return commands.validate(payload, cfg, seen or commands.SeenIds(), latest, now=NOW)


def test_accepts_valid_command(cfg):
    v = run(cfg, msg())
    assert v.status == "accepted" and v.command.name == "motor_start"


def test_rejects_when_control_disabled(cfg):
    cfg.control_enabled = False
    v = run(cfg, msg())
    assert v.status == "rejected" and "disabled" in v.reason


def test_rejects_unknown_command(cfg):
    v = run(cfg, msg(command="write_register_40011"))
    assert v.status == "rejected" and "not allowed" in v.reason


def test_expired(cfg):
    v = run(cfg, msg(expires_at="2026-11-03T09:59:59Z"))
    assert v.status == "expired"


def test_rejects_long_ttl(cfg):
    v = run(cfg, msg(expires_at=(NOW + timedelta(minutes=5)).isoformat()))
    assert v.status == "rejected" and "more than" in v.reason


def test_rejects_naive_timestamp(cfg):
    v = run(cfg, msg(expires_at="2026-11-03T10:00:10"))
    assert v.status == "rejected"


def test_duplicate_cmd_id_runs_once(cfg):
    seen = commands.SeenIds()
    assert run(cfg, msg(), seen=seen).status == "accepted"
    v = run(cfg, msg(), seen=seen)
    assert v.status == "rejected" and "duplicate" in v.reason


def test_local_mode_rejected(cfg):
    v = run(cfg, msg(), latest={"mode": "LOCAL"})
    assert v.status == "rejected" and "LOCAL" in v.reason


def test_no_reading_rejected(cfg):
    v = run(cfg, msg(), latest=None)
    assert v.status == "rejected"


@pytest.mark.parametrize("payload", ["not json", "[]", json.dumps({"command": "motor_start"})])
def test_malformed(cfg, payload):
    assert run(cfg, payload).status == "rejected"
