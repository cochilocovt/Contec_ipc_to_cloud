# Data contract

The gateway, the cloud services and the web app agree on what follows. The gateway hardware can change (BX-220, Raspberry Pi, another PLC); only the tag map in `gateway.yaml` is specific to the machine.

## Topics

```
factory/{site}/{machine_id}/telemetry   gateway → cloud   every poll, QoS 1
factory/{site}/{machine_id}/state       gateway → cloud   retained latest snapshot
factory/{site}/{machine_id}/status      gateway → cloud   retained online/offline (Last Will)
factory/{site}/{machine_id}/cmd         cloud → gateway   QoS 1
factory/{site}/{machine_id}/cmd/ack     gateway → cloud   QoS 1
```

## Telemetry

```json
{
  "ts": "2026-10-31T01:15:12.250Z",
  "machine_id": "press-01",
  "seq": 18234,
  "metrics": {
    "motor_running": true,
    "motor_speed_rpm": 1450,
    "motor_current_a": 12.4,
    "spindle_temp_c": 61.2,
    "mode": "REMOTE",
    "part_count": 3482,
    "fault_code": 0
  }
}
```

- `ts` is UTC with `Z`.
- `seq` increases by one per poll and restarts at 1 when the gateway restarts. A gap without a restart means lost messages.
- Counters such as `part_count` are cumulative, so a dropped message loses nothing.
- `state` carries the same fields plus `"plc": "ok"`, or `"plc": "unreachable"` with no metrics when a read fails.

## Status

```json
{"state": "online", "ts": "2026-11-03T15:33:01.013Z"}
```

`offline` is published on clean shutdown, and by the broker as the Last Will if the gateway dies.

## Command

```json
{
  "cmd_id": "c7f3a2e1-4b2d-4e8a-9f1c-2d6b8e0a7c11",
  "command": "motor_start",
  "params": { "motor": "M1" },
  "issued_by": "operator@client.com",
  "issued_at": "2026-10-31T01:15:20Z",
  "expires_at": "2026-10-31T01:15:30Z"
}
```

- `cmd_id`: unique string up to 64 characters. A repeated id runs once.
- `command`: must be listed under `control.commands` in the gateway config.
- `expires_at`: ISO 8601 with a UTC offset, in the future, and no more than `max_ttl_s` away (default 30 s).
- `params` is carried for the audit trail; the current gateway ignores it.

## Acknowledgement

```json
{"cmd_id": "c7f3a2e1-...", "status": "rejected", "reason": "machine in LOCAL mode", "ts": "2026-10-31T01:15:20.410Z"}
```

| status | meaning |
|---|---|
| `accepted` | passed every gateway check; about to write |
| `executed` | the write to the PLC succeeded (not proof the machine moved) |
| `rejected` | failed a check or the PLC write failed; `reason` says which |
| `expired` | arrived after `expires_at` |

A valid command produces two acks: `accepted` then `executed` (or `rejected` if the write fails).

## Tag map

```yaml
read:
  motor_running:   { type: coil,    address: 0 }
  motor_current_a: { type: holding, address: 101, scale: 0.1 }
  mode:            { type: holding, address: 103, enum: { 0: LOCAL, 1: REMOTE } }
  part_count:      { type: holding, address: 104, format: uint32 }
control:
  commands:
    motor_start: { type: coil, address: 10, pulse_ms: 500 }
```

- `type`: `coil`, `discrete`, `holding` or `input`.
- `format` (registers only): `uint16` (default), `int16`, `uint32`, `int32`, `float32`. Two-word formats use big-endian word order; change the decoder if the PLC differs.
- Addresses are 0-based protocol addresses. Holding register 40101 in PLC documentation is usually address 100 here.
- Commands are either a coil (pulsed or set to a fixed `value`) or a holding register with a fixed `value`. The cloud cannot pass a value.

## Database (TimescaleDB)

```sql
CREATE TABLE telemetry (
  ts          timestamptz NOT NULL,
  machine_id  text        NOT NULL,
  metric      text        NOT NULL,
  value       double precision,
  value_text  text,             -- enums such as mode
  seq         bigint
);
SELECT create_hypertable('telemetry', 'ts');
CREATE INDEX ON telemetry (machine_id, metric, ts DESC);

CREATE TABLE commands (
  cmd_id      text PRIMARY KEY,
  machine_id  text        NOT NULL,
  command     text        NOT NULL,
  params      jsonb,
  issued_by   text        NOT NULL,
  issued_at   timestamptz NOT NULL,
  expires_at  timestamptz NOT NULL,
  status      text        NOT NULL DEFAULT 'sent',  -- sent, accepted, executed, rejected, expired, confirmed
  reason      text,
  updated_at  timestamptz NOT NULL DEFAULT now()
);
```

The `commands` table doubles as the audit log. `confirmed` is set by the backend when telemetry shows the expected change.
