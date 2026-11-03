-- Runs once, when the database volume is first created.
-- To re-run after changing it: docker compose down -v (deletes all data).

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- One row per metric per reading. See docs/data-contract.md.
CREATE TABLE telemetry (
  ts          timestamptz NOT NULL,
  machine_id  text        NOT NULL,
  metric      text        NOT NULL,
  value       double precision,   -- numbers; booleans as 0/1
  value_text  text,               -- enums such as mode
  seq         bigint
);
SELECT create_hypertable('telemetry', 'ts');
CREATE INDEX telemetry_machine_metric_ts ON telemetry (machine_id, metric, ts DESC);

-- Latest online/offline state per gateway.
CREATE TABLE gateway_status (
  machine_id  text PRIMARY KEY,
  site        text        NOT NULL,
  state       text        NOT NULL,   -- online | offline
  ts          timestamptz,            -- from the message; null for the broker's Last Will
  received_at timestamptz NOT NULL DEFAULT now()
);

-- Every command sent, with its latest status. Doubles as the audit log.
CREATE TABLE commands (
  cmd_id      text PRIMARY KEY,
  site        text        NOT NULL,
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
CREATE INDEX commands_machine_issued ON commands (machine_id, issued_at DESC);

-- Every ack exactly as received, in order.
CREATE TABLE command_events (
  id          bigserial PRIMARY KEY,
  cmd_id      text,
  machine_id  text        NOT NULL,
  status      text        NOT NULL,
  reason      text,
  ts          timestamptz,
  received_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX command_events_cmd ON command_events (cmd_id);
