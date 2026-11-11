# ipc_connection

Edge gateway project: a Contec BX-220 box PC reads a manufacturing machine's PLC over Modbus and publishes to an MQTT broker; later it runs allowlisted start/stop commands from a cloud web app. Owner: Vaibhav.

## Main repository

`https://github.com/cochilocovt/Contec_ipc_to_cloud` is the canonical repository; this folder is its local checkout. Start by checking git status and fetching origin. Fast-forward only when the working tree is clean and the branch has no divergent work; otherwise preserve it and reconcile deliberately. Finish authorized working sessions by committing and pushing the project changes and session log here. Never force-push or include unrelated changes or secrets.

## How to work: lead and workers

The main session (GPT 6.1 Sol, `gpt-6.1-sol`) is the lead and owns the project: plans, design, safety, explanations to the owner, review, commits. Two GPT 6 Luna workers (`gpt-6-luna`, low reasoning) in `.codex/agents/` do deterministic tasks. The owner wants delegation used as described here.

- Start every session by reading `docs/log/open-items.md`, then state a short numbered plan. Mark each step `lead`, `luna_runner` or `luna_scout`.
- `luna_runner` (edits files, runs commands): run tests and report; apply an edit you've written out exactly; formatting; regenerate a file from a template you give; `docker compose config`; git status/diff summaries; log entries from text you wrote.
- `luna_scout` (read-only): find files, functions, config keys and usages; fetch a named documentation page and extract specific facts with quotes.
- Keep with the lead, never delegate: anything in the machine-control write path or its safety rules; data contract, schema or tag-map design; security; debugging when the cause is unclear; choosing between options; anything on the owner's computer through the device bridge; commits, pushes and anything irreversible; every explanation to the owner.
- Write each brief with: goal, exact paths and commands, the exact text of any edit, what to return, done-when, and what not to touch. Spawn with no conversation history (`fork_turns="none"` when supported); the brief must be self-contained. Use the named custom role so its model and instructions load. If the role is unavailable, do not silently use a built-in role or another model: report the limitation and do the step as lead.
- Verify before relying on a result: re-run the check or read the changed lines yourself. If a worker reports `blocked`, guessed, or deviated, do that step yourself.
- Don't delegate what you can do in one or two tool calls; starting a worker costs more than that. Run at most three workers at once, only on independent tasks. Workers must never spawn their own workers.
- Finish every session by updating the log (see "Keeping the log"), then commit and push yourself.

### Evidence, handoffs and acceptance

Follow [docs/agent-workflow.md](docs/agent-workflow.md) for both teams. Assign a task ID, dependencies, exact owned paths/commands, source hashes and replacement counts, preflight, artifact path, output limit and executable acceptance checks. Workers read that document in their bounded context. Check tools/access early; a probe does not guarantee later policy approval. On denial, stop and report the exact operation/error and partial changes; never bypass policy or silently switch roles/models.

Require measured byte sizes (or explicitly unavailable), path/line excerpts and distinct found/empty/not-found/unreadable outcomes. Reports stay within 6,000 characters and quoted lines within 240; full approved non-secret runner output stays under ignored `logs/agent-runs/`. Use `tools/agent_task.py` for read-only evidence/preflight, UTF-8 command capture, hash/count-checked exact edits and lead-authored acceptance plans. A worker's `done` is not lead acceptance. Verify independently, including expected changed paths and secret exclusion.

Use `tools/check_home_lab.py` for read-only service/port/Grafana/database checks; request `--machine` explicitly to check freshness. The lead interprets failures and chooses repairs. After review, the lead records actual task timing, outcome and correction time with `agent_task.py record`; summarize with `scorecard`. Workers never grade their own result or edit the ledger. Record observed tokens only and assess several sessions before changing models. Helpers are not security boundaries.

## Working style

- Explain in plain language, step by step, and assume the owner is new to industrial controls when explaining hardware, PLCs or networking.
- State assumptions and uncertainty plainly; look up anything that changes over time (prices, versions, support dates) instead of relying on memory.
- Never claim something works until you've tested it; say what was tested and what wasn't.

## Where things are

- `gateway/ipc_gateway/` the gateway: `config.py` (YAML loading and validation), `plc.py` (Modbus reads and writes, value decoding), `commands.py` (allowlist, expiry, dedupe, mode check), `app.py` (main loop, MQTT).
- `gateway/config/gateway.example.yaml` the tag map and settings. Real `gateway.yaml` is git-ignored.
- `tools/sim_plc.py` simulated PLC with the same register map. `tools/send_command.py` bench command sender.
- `cloud/` home-lab stack: `docker-compose.yml` (Mosquitto, TimescaleDB, ingest, Grafana), schema in `db/init/01-schema.sql`, ingest in `ingest/ingest.py`, dashboard in `grafana/dashboards/machine.json`.
- `docs/log/` project log: `timeline.md` (every session), `open-items.md` (current state and next steps), `topics/` (one file per subject). Read `open-items.md` first to see where things stand.
- `docs/` architecture, home-lab setup, data contract, hardware notes, decision log. Update `docs/decisions.md` when a decision changes.
- `.codex/agents/` the two Luna worker definitions; `.codex/config.toml` sets the Sol lead, Luna defaults, three-worker limit and one-level spawn depth. See `docs/codex-agents.md` for source mapping, use cases and permission differences.
- `.claude/agents/` and `.claude/settings.json` retain the independent Claude setup.

## Known pitfalls

- pymodbus 3.11 uses `device_id=`, not `slave=`.
- The IPC runs Windows 10 version 1607 (build 14393): no built-in OpenSSH server, old PowerShell 5.1, Unified Write Filter may discard changes at reboot.
- Git in the owner's Windows folder through the device bridge leaves `.lock` and `tmp_obj_*` files under `.git` unless delete permission is granted first; clean them up after every git command there. Do not delete another active process's lock or temporary files.
- The home-lab broker has no auth; the gateway's `control.enabled` is `false` until the plant signs off.

## Commands

- Tests: `python -m pytest`, working directory `gateway/`.
- Cloud stack: keep an existing `cloud/.env`; on first setup copy `.env.example` and set passwords/broker address, then run `docker compose up -d --build` from `cloud/`. Grafana on localhost:3000. Schema changes may need a migration; `docker compose down -v` wipes data and requires specific authorization.
- Bench run: start the broker, `python tools/sim_plc.py --port 5020`, then `python -m ipc_gateway --config config/gateway.yaml` from `gateway/`.
- On PowerShell 5.1 use separate commands or the tool's working-directory setting instead of `&&`.

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

## Home lab

This PC runs `cloud/`; a spare Windows laptop runs the simulated PLC (`tools/run-sim.bat`); the BX-220 runs the gateway. A Keyence KV-8000 is on hand for one session of real-PLC testing later (Host Link on port 8501; Modbus TCP support unconfirmed). The final machine uses a different PLC: a Keyence KV-X310 on a pump volumetric test rig, designed in `docs/pump-test-rig/` (kept separate from the home lab; don't change home-lab files for it).

The home-lab broker is open (no TLS, no auth). Never expose it beyond the LAN.

## Keeping the log

After each working session, append an entry to `docs/log/timeline.md` (date, question, short answer, repo changes) and update `docs/log/open-items.md`. Put new detail in the matching `docs/log/topics/` file. Record prices and support dates with the date checked. Never put passwords, keys or personal contact details in the log.

## Open questions

Client rig (see `docs/pump-test-rig/client-questions.md`): servo and load cell details, what "load cell adjustment" means, target output and tolerance, KV-X310 protocol (OPC UA proposed) and ladder variables. Also: production cloud platform; ESU from Contec.

## Agent parity

This is the Codex counterpart of `CLAUDE.md` and `.claude/agents/haiku-{runner,scout}.md`, based on source commit `c12ca02`. Preserve their responsibilities and use cases when updating either setup. Worker nesting is forbidden by instructions and capped by `agents.max_depth = 1` in the project configuration. Codex custom agents inherit parent permissions, so read-only scouting is a behavioral restriction, not a separate worker sandbox. Never delegate work that requires relying on a hard worker-specific security boundary.
