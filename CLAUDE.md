# ipc_connection

Edge gateway project: a Contec BX-220 box PC reads a manufacturing machine's PLC over Modbus and publishes to an MQTT broker; later it runs allowlisted start/stop commands from a cloud web app. Owner: Vaibhav.

## Where things are

- `gateway/ipc_gateway/` the gateway: `config.py` (YAML loading and validation), `plc.py` (Modbus reads and writes, value decoding), `commands.py` (allowlist, expiry, dedupe, mode check), `app.py` (main loop, MQTT).
- `gateway/config/gateway.example.yaml` the tag map and settings. Real `gateway.yaml` is git-ignored.
- `tools/sim_plc.py` simulated PLC with the same register map. `tools/send_command.py` bench command sender.
- `docs/` architecture, data contract, hardware notes, decision log. Update `docs/decisions.md` when a decision changes.

## Commands

- Tests: `cd gateway && python -m pytest`
- Bench run: start Mosquitto, `python tools/sim_plc.py --port 5020`, then `cd gateway && python -m ipc_gateway --config config/gateway.yaml`

## Target environment

- BX-220D-DC781724: Atom E3845, 4GB, 2x CFast, 2x GbE, 2x RS-232C, 10.8–31.2V DC.
- OS stays Windows 10 IoT Enterprise 2016 LTSB (owner's decision). Support ended 2026-10-13; ESU only via Contec. May run the Unified Write Filter.
- Python 3.10+ 64-bit. Dependencies are pinned in `gateway/requirements.txt`; pymodbus 3.11 uses `device_id=`, not `slave=`.
- Runs as a Windows service under NSSM. Keep it Windows-compatible: no Linux-only calls, use `pathlib`.

## Rules for the write path

- The PLC is the authority. The gateway only requests. Never add logic that bypasses PLC interlocks or touches the E-stop.
- Only commands listed under `control.commands` can be written. No generic "write register" command, ever.
- Every command needs `cmd_id` and an `expires_at` with a UTC offset, no further out than `max_ttl_s`. Duplicates run once.
- `control.enabled` stays `false` in the example config. Remote control goes live only after the plant signs off the control design.
- A command is "executed" when the write succeeds; the UI must wait for telemetry to confirm the machine actually changed.

## Conventions

- All timestamps UTC, ISO 8601 with `Z`.
- Topics: `factory/{site}/{machine_id}/{telemetry|state|status|cmd|cmd/ack}`. See `docs/data-contract.md` before changing a payload.
- Counters such as `part_count` are published cumulative.

## Open questions

PLC make, model and protocol (Ethernet or RS-232); register map; cloud platform; whether the old HMI keeps running; ESU from Contec.
