# Shared agent workflow upgrades

## 2026-11-11

The owner asked to apply all first-use improvements to both Sol/Luna and Opus 5.5/Haiku 5.5. The shared contract is [../../agent-workflow.md](../../agent-workflow.md), referenced by both lead files and all four worker definitions.

### Added

1. Evidence with exact path/line excerpts, measured metadata or explicit unavailable values, and separate found/empty/not-found/unreadable outcomes. No guessed or unrequested metadata.
2. Self-contained task IDs, dependencies, owned paths, early capability checks and exact blocked-operation handback. No permission bypass or silent model/role substitution.
3. Reports capped at 6,000 characters and quoted lines at 240; approved non-secret runner artifacts under ignored `logs/agent-runs/`. Scouts remain read-only.
4. `tools/agent_task.py`: Windows-compatible UTF-8, shell-free command capture; working-directory-aware executable resolution; hash/count-checked exact edits preserving BOM/newline conventions; read-only evidence/preflight.
5. Lead-authored executable acceptance checks for command output hashes/zero exits, expected file hashes/text counts and optional whole-checkout changed-file scope. Workers cannot accept or grade themselves.
6. `tools/check_home_lab.py`: read-only Compose/services, safe published bindings, TCP, Grafana HTTP, database SELECT and optional online/fresh telemetry checks. No MQTT publications, PLC connections, credentials reads or service changes.
7. Lead-owned `delegation-scorecard.jsonl` and summary: observed task outcomes, timing, correction work and optional token counts. Missing timestamps/tokens remain explicit; an observed duration can be recorded without inventing UTC timestamps. Outcomes include orchestration failures and are not model-quality or cost comparisons.

### Validation and observed failures

- Final tools suite: **18 tests passed**. Covers missing/unreadable/minified evidence, secret/path guards, probe collisions, stale hashes/count mismatches before edits, Unicode/BOM/CRLF, command failure/timeout, Windows cwd resolution, bounded parseable output, acceptance tampering/scope, unknown timing, duplicate/invalid metrics, stale/future/offline telemetry and unsafe broker bindings without connecting to them.
- Gateway regression suite: **18 passed**. No gateway, PLC write path, example control setting, data contract, database schema, models, effort settings or tool allowlists changed.
- Both Luna roles exercised the new contract explicitly in this existing session. Scout returned the actual README evidence; runner completed the tools/gateway tests and live service checks. Final output hashes and source references were independently checked by the lead.
- The initial runner validation stopped on a Windows executable-resolution bug in the lead's new helper. The lead fixed it, added a regression test, and the retry passed. The scorecard records the original blocked task and its cause.
- Claude CLI setup/auth checks succeeded. A live Opus run loaded both named project Haiku roles; the CLI's model-usage metadata reported `claude-opus-5-5` and `claude-haiku-5-5`. This is runtime metadata, not independent backend attestation. Existing model/effort settings and tool restrictions were preserved.
- Haiku Runner's live read-only health check passed. Opus independently read its artifacts, and the outer lead verified the output hash and service facts. The runner appended an unnecessary exit-code echo; this deviation is noted in the scorecard.
- Opus caught an unsupported, unrequested total-line-count claim from Haiku Scout. The original report is recorded as rejected even though its main README facts were correct. Both scout definitions now explicitly forbid guessed/unrequested numeric metadata. A targeted live Haiku Scout recheck returned the requested facts correctly and marked unavailable byte/hash/time metadata honestly.
- The first targeted recheck failed before a worker started because the lead supplied a positional prompt after a variadic CLI option. Passing the same prompt through stdin succeeded without changing permissions/models; the launcher failure is recorded separately.
- Infrastructure health passed on the running home-PC stack. Requesting `--machine setup-check` correctly failed because that temporary gateway is offline and its data is stale. The full physical three-device path and machine-control operation were not tested or changed.

### Operating limits

Start a fresh Codex chat to load the changed custom role definitions. Reused workers in this session were explicitly told to read/apply the new contract; file edits alone do not prove a running chat reloaded. Claude's existing project definitions were exercised in fresh CLI invocations.

The helpers are convenience checks, not a security sandbox or a guarantee that later commands will pass policy. Exact edits across several files are not transactional. Native Haiku Scout keeps Bash disabled and hands unavailable measurements to the lead. Continue independent review: this session demonstrated that instructions alone do not eliminate unsupported claims.

The initial scorecard records this session's new measured tasks only. Token counts are left null at individual-task granularity; aggregate CLI token/cost figures were not assigned to workers or used to claim savings. Timing notes distinguish delegation, command and CLI startup intervals; compare only like scopes after several sessions.

References checked 2026-11-11: [OpenAI subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Claude Code subagents](https://code.claude.com/docs/en/sub-agents).
