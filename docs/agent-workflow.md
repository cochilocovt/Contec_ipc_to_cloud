# Shared lead and worker workflow

Applies to Sol/Luna and Opus 5.5/Haiku 5.5. Keep the existing models, low worker effort, tool restrictions, three-worker concurrency limit and no worker nesting. The lead owns decisions, unclear debugging, security, machine-control work, data design, device-bridge operations, final explanations, commits and pushes. Helpers do not grant authority or bypass tool policy.

## Handoff and capability check

The lead gives each independent task a short unique `task_id` and a self-contained brief containing:

- Goal and dependencies; wait for prerequisites before dispatch.
- Exact repository-relative owned paths, working directory and executable/argument list. State that others share the checkout.
- Complete old/new edit text, replacement counts and source SHA-256 hashes when editing. No inferred substitutions.
- Required tools and a small preflight; identify any exact disposable write-probe path and authorize its creation/deletion explicitly.
- Explicit acceptance checks and expected files/outputs; include the known baseline if checking the whole checkout's changed paths.
- Exact ignored artifact directory under `logs/agent-runs/TASK_ID/`, output limits, and what must not be touched.

Check tools, input access and working directory before expensive work. Runners can use `agent_task.py preflight`; an optional write probe tests that exact location at that moment. Scouts use read-only evidence or native Read/Grep/Glob. Haiku Scout keeps Bash disabled: metadata it cannot obtain is `not measured`, and the lead obtains byte sizes/hashes if needed. Do not add tool permissions to satisfy a preflight. It cannot guarantee that a later command will pass policy.

If blocked, stop and return the exact failing operation, working directory, exit code/error, any partial changes and the last verified checkpoint. Do not guess, retry indefinitely, change permissions, switch models/roles or find another execution route around a denial. The lead reviews the reason, narrows or corrects the task, or performs an independently authorized step within the applicable policy. Denials still apply to the lead.

Keep one- or two-call tasks with the lead. Reuse a worker for related bounded tasks. Assign disjoint files for concurrent edits and reread/re-hash before writing if another agent changed a dependency.

## Evidence and bounded output

Every local finding includes its exact path, line range, short verbatim excerpt and byte size when measured. Include SHA-256 for edit inputs. Report only requested facts; every numeric metadata claim requires a direct tool measurement. Never guess total lines, byte sizes or timing, and omit unrequested metadata. Separate `found`, `empty` (verified zero bytes), `not_found` (searched scope or missing path), and `unreadable` (access/decoding failure). A blank tool response or a failed search does not establish an empty file. Web findings include an official URL, short quote and date/version if shown; respect quotation limits.

Return at most **6,000 characters** per worker report. Each quoted line is at most **240 characters**; mark shortened excerpts explicitly. Never print a whole minified file, resolved Compose configuration, environment dump or secret. Request a narrower range when needed. Runners keep approved non-secret full command output in the exact ignored artifact directory and return its path, exit code, summary and bounded error excerpts. Long failures remain in the artifact; report truncation honestly. Scouts do not create artifacts or redirect output.

Runner report:

```text
Task: TASK_ID
Result: done | blocked
Started / finished: UTC timestamps with Z
What I did: brief steps; exact command and cwd
Exit code: integer, or not run / unavailable
Checks: names and pass/fail; never claim an unrun check
Artifacts: exact local paths, or none
Changed files: exact list, or none; mention partial work on failure
Output: bounded summary / excerpts, with truncation noted
Unexpected: facts, or nothing
```

Scout report uses the same Task, Result, timestamps and Unexpected fields, then `Found`, `Not found`, `Unreadable`, `Uncertain`; each finding carries the evidence above. Missing metadata is explicit. Worker `done` is a proposal for acceptance; only the lead marks it accepted.

## Windows helpers and executable acceptance

Use Python 3.10+ and argument lists, not shell-built commands. JSON plans are UTF-8 (BOM accepted), generated files are UTF-8, and exact edits preserve an existing BOM and CRLF/LF convention. PowerShell 5.1 commands run separately or with an explicit working directory. Capture output without printing secrets. These scripts require no new packages.

From the repository root (on this PC use `gateway/.venv/Scripts/python.exe` in place of `python`):

```powershell
python tools/agent_task.py evidence docs/guide-src/README.md --start 1 --end 12
python tools/agent_task.py preflight --read docs/agent-workflow.md --command python --command docker
python tools/agent_task.py run --cwd gateway --artifact logs/agent-runs/TASK_ID -- python -m pytest
python tools/agent_task.py edit logs/agent-runs/EDIT_ID/plan.json
python tools/agent_task.py accept logs/agent-runs/EDIT_ID/accept.json
python tools/agent_task.py scorecard
```

`run` creates a new artifact directory exclusively, uses no shell, resolves a relative executable against the requested working directory on Windows, records UTC times/elapsed seconds/exit code, captures non-secret output as `output.txt`, and writes `result.json` with its hash. It reports timeout or execution failures as blocked. Supply only lead-approved commands; it is an execution wrapper, not a command allowlist or security sandbox. Never use it for commands that might emit credentials (for Compose validation use `config --quiet`). A timeout stops the direct child; do not use this wrapper to launch background services or processes with independent children.

`preflight --write-probe logs/agent-runs/EDIT_ID/probe.tmp` exclusively creates/deletes that exact file in an existing directory. The brief must name and authorize it. A pre-existing file is left untouched and causes failure.

Exact-edit plan (`sha256` is the **raw original file** hash):

```json
{"files": [{"path": "docs/example.md", "sha256": "ACTUAL_SOURCE_HASH", "replacements": [{"old": "before", "new": "after", "count": 1}]}]}
```

The helper checks all files/counts before the first write, checks for concurrent changes, and reads each result back. It edits existing files only. Writes across multiple files are not transactional: if I/O fails during writing, inspect the named files before retrying. Paths stay inside this checkout and secret/Git-internal paths are refused. This is a convenience guard, not a replacement for role restrictions.

Acceptance plan:

```json
{"run_results": ["logs/agent-runs/TASK_ID/result.json"], "files": [{"path": "docs/example.md", "sha256": "EXPECTED_FINAL_RAW_HASH", "contains": [{"text": "after", "count": 1}]}], "expected_changed_paths": ["docs/example.md"]}
```

Use only applicable fields. At least one check is required. Run checks require zero exit code and unchanged output hash; file checks require the lead's expected final hash and optional exact text counts. `expected_changed_paths`, when supplied, checks all tracked changes relative to HEAD plus non-ignored untracked files, including known pre-existing work. It does not prove who changed a file. The lead creates/reviews the expected result independently, reads changed lines or reruns a meaningful check, and reviews scope/secrets before committing. Workers cannot accept their own work by inventing expected hashes after editing.

## Reusable project health check

```powershell
python tools/check_home_lab.py
python tools/check_home_lab.py --machine press-01 --max-age-s 30
```

Checks Compose validity, required containers/DB health, published addresses and TCP ports, Grafana HTTP health, and a read-only database query. With `--machine`, also requires online status and telemetry age between zero and the supplied limit. Without it, freshness is explicitly **not checked**. An offline `setup-check` test machine should fail freshness; that is expected. Exit 0 means the requested scope passed; exit 1 means a check failed.

The checker reads no `.env`/credentials, container environments or PLC registers; it publishes no MQTT messages and changes no services. It does not verify the Grafana datasource's password, firewall traversal from another device, a physical machine or command execution. The lead interprets failures and chooses repairs.

## Delegation scorecard

The lead records each reviewed task once in `docs/log/delegation-scorecard.jsonl` with `python tools/agent_task.py record logs/agent-runs/REVIEW_ID/score.json`. Workers return timing/evidence but never edit or grade the ledger. No retrospective invented timings, token estimates, prices or savings. Start measuring new tasks; historical runs can remain unmeasured.

```json
{"task_id": "20261111-example", "team": "codex", "role": "luna_runner", "started_at": "2026-11-11T01:00:00Z", "finished_at": "2026-11-11T01:01:00Z", "outcome": "accepted", "lead_rework_minutes": 0, "tokens": null, "notes": "Example only; use actual observed times."}
```

`team` is `codex` or `claude`; roles are `luna_runner`/`luna_scout` or `haiku-runner`/`haiku-scout`. Outcomes are `accepted`, `blocked`, `rejected`. Rework minutes are lead-observed time correcting the result (not ordinary review); tokens are observed counts or null. Notes are at most 240 characters, with no credentials or personal details. IDs are unique and duplicate appends fail. Elapsed seconds are derived from supplied UTC times; record whether those measure command execution or dispatch-to-report in notes. If timestamps are unavailable, set both to null; an optional `observed_elapsed_s` may hold a duration directly exposed by the runtime. Otherwise elapsed time remains null and the summary reports coverage. Never back-calculate fictional timestamps or attach aggregate token usage to individual workers.

The summary groups outcomes, elapsed time, lead rework and observed token coverage by team. Outcomes cover the whole handoff: a blocked task may be caused by the lead's brief or launcher, not by the worker. Keep that cause in notes. Parallel wall times overlap; this is not a cost comparison. Review after several sessions before changing task sizes, roles or models.

## Loading updated instructions

Read this document in each worker's bounded context. Existing Codex chats can retain loaded definitions; start a fresh chat to load changed role files. Explicitly include updated requirements when reusing a worker already loaded in the current session. Claude's documented existing-file reload behavior differs; verify runtime loading rather than assuming either team changed models. Keep model claims separate from independent backend attestation.

References checked 2026-11-11: [OpenAI custom subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Claude Code custom subagents](https://code.claude.com/docs/en/sub-agents).
