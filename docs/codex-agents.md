# Codex lead and workers

The main repository is [cochilocovt/Contec_ipc_to_cloud](https://github.com/cochilocovt/Contec_ipc_to_cloud). Keep the local checkout, session log and pushed repository in sync through normal fetch, review, commit and push operations. Never force-push or include unrelated work.

## Source and mapping

The requested `.claude/agents.md` is a directory in this repository: `.claude/agents/`. This setup reproduces both worker definitions plus the orchestration rules in `CLAUDE.md`, as of commit `c12ca02` on 2026-11-11. The Claude files remain available independently.

| Claude role | Codex role | Model | Reasoning | Responsibility |
|---|---|---|---|---|
| Main Opus 5.5 session | Main Sol session, governed by `AGENTS.md` | `gpt-6.1-sol` | medium | Own the project, plan, design, decide, review, explain, commit and push |
| `haiku-runner` | `luna_runner`, `.codex/agents/luna-runner.toml` | `gpt-6-luna` | low | Execute fully specified commands and exact edits |
| `haiku-scout` | `luna_scout`, `.codex/agents/luna-scout.toml` | `gpt-6-luna` | low | Find sourced facts without changing files |

`.codex/config.toml` sets the lead model, worker defaults, live documentation search, a limit of three concurrent workers (excluding the lead) and `agents.max_depth = 1` to stop workers spawning their own workers. The installed Codex 0.166.0 runtime exposes this depth setting in its effective configuration. The two standalone agent files explicitly pin Luna and low reasoning, so they do not inherit the lead's effort accidentally.

## Same use cases

| Task | Owner | What the brief must specify |
|---|---|---|
| Run tests and report | `luna_runner` | `gateway/`, `python -m pytest`, expected completion and required output |
| Apply an exact edit | `luna_runner` | Exact owned paths, old text and complete new text; stop if it does not match |
| Formatting | `luna_runner` | Exact formatter command and file list; no unrelated formatting |
| Regenerate from a template | `luna_runner` | Complete template, substitutions, output path and verification |
| Validate Compose configuration | `luna_runner` | `cloud/`, `docker compose config --quiet`; never print resolved secrets or read `.env` |
| Summarise Git state | `luna_runner` | Read-only `git status`/`git diff` commands and requested scope |
| Write a session-log entry | `luna_runner` | Exact entry text written by the lead and exact destination |
| Find files/functions/config/usages | `luna_scout` | Search names, path scope and required path:line evidence |
| Extract named facts from documentation | `luna_scout` | Named official URL, specific questions and short quoted evidence; include date/version when shown |

The lead keeps machine-control write-path work and safety rules, data-contract/schema/tag-map design, security, unclear debugging, choosing options, device-bridge operations, irreversible actions, commits, pushes and every explanation to the owner. The runner retains the source definition's exact-text protection for sensitive files; that does not transfer responsibility for these decisions to a worker.

Read `docs/log/open-items.md` first, then give a numbered plan with each step assigned. Every worker brief includes the goal, exact paths and commands, exact edit text if relevant, what to return, done-when and what not to touch. Workers receive no conversation history (`fork_turns="none"` where supported). They share the checkout, must preserve concurrent changes and return `blocked` instead of guessing. The lead reads changed lines or reruns checks before relying on results. A task taking only one or two tool calls stays with the lead.

Both teams follow [the shared workflow](agent-workflow.md), including task IDs, timestamps or explicit unavailable timing, preflight, evidence, bounded artifacts, lead-authored executable acceptance and the lead-owned delegation scorecard. Reports are at most 6,000 characters; quoted lines at most 240. Full approved non-secret runner output stays under ignored `logs/agent-runs/`; scouts create no artifacts. Missing files, unreadable files and verified zero-byte files are distinct outcomes. Neither worker may read secrets, delegate, launch another agent CLI, alter Git history/branches, send messages externally or control the owner's desktop.

## Shared operational upgrades

`tools/agent_task.py` provides read-only evidence/preflight, exact edits with source hashes and match counts, shell-free UTF-8 command capture, acceptance checks and scorecard recording/summary. `tools/check_home_lab.py` checks services, published ports, Grafana HTTP health, database reads and optional telemetry freshness without publishing MQTT or touching a PLC. Examples and limitations are in [agent-workflow.md](agent-workflow.md).

Haiku Scout retains its native Read/Grep/Glob tools and Bash denial. It reports byte sizes/hashes/timestamps it cannot measure as unavailable; the lead measures them separately. Codex Scout can use the helper's read-only evidence/preflight modes. This keeps responsibilities aligned while respecting the runtimes' different tool surfaces. Models and worker effort stay unchanged.

## Starting and using the setup

Start a fresh Codex chat or CLI session in the repository after adding these files. Project configuration must be trusted before Codex loads it. Existing chats may retain their original model and loaded role list; select GPT 6.1 Sol in the composer for the lead if needed. Do not assume a file edit switches an already running chat.

For example:

> Have luna_scout find every use of max_ttl_s in gateway/, report path and line numbers, and change nothing. Use no conversation history.

> Have luna_runner run python -m pytest from gateway/, report the exit code, summary and full failures, and make no source edits. Use no conversation history.

If the named roles are unavailable, the lead reports that limitation and performs the task directly. Do not silently substitute a generic agent or another model. Custom roles outside this project are unrelated and must not replace these workers.

## Permission differences

Claude has per-agent tool allowlists and `disallowedTools: Agent`. Codex custom agents inherit parent permissions and MCP servers; custom instructions do not create a separate read-only sandbox. The scout needs shell access for local file search/reading because Codex does not expose the same Read/Grep/Glob tool set as Claude. Its instructions prohibit all mutations and restrict commands to reading/searching. Both workers disable apps, plugins, memories and permission-request tools, while retaining the shell needed for their local tasks.

The no-nesting instructions are backed by the project's one-level spawn-depth setting. Read-only scouting remains an instruction-level restriction. Do not treat it as hard security isolation or delegate a task that depends on that isolation. The three-worker cap applies to concurrency; the depth cap applies to nesting. Do not copy Claude's nesting environment variable into Codex.

## Verification on 2026-11-11

- Codex CLI 0.166.0 loaded `AGENTS.md` and both named custom roles in a fresh session. Its effective configuration selected `gpt-6.1-sol` at medium reasoning, `gpt-6-luna` worker defaults at low reasoning, three concurrent workers and one-level spawn depth.
- Both agent TOML files explicitly selected `gpt-6-luna` at low reasoning. Backend model identity was not independently attested by the test; model claims here describe the resolved configuration.
- `luna_scout` returned correct source lines for the gateway test command and `max_ttl_s`; the lead independently checked them.
- `luna_runner` applied an exact `before` to `after` replacement in a disposable fixture, read it back and reported success. The lead independently verified the complete text and final newline, then removed the fixture.
- All three TOML files parsed successfully in the lead session. The initial read-only sandbox smoke test blocked the runner's Python startup; the runner reported `blocked` without guessing. The exact-edit test used the parent workspace-write permission mode.
- The machine-control safety section matches `CLAUDE.md` verbatim, and local documentation links resolve. No gateway application code or hardware behavior changed; the gateway test suite and physical PLC were not retested for this configuration-only change.

## Maintaining parity

When changing `CLAUDE.md` or `.claude/agents/`, compare `AGENTS.md` and both `.codex/agents/` files in the same change. Preserve role boundaries, use cases, exact-edit safeguards, secret handling and report formats. Keep the model mapping explicit; never replace an explicitly chosen model with a different tier.

References checked 2026-11-11: [official custom-agent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents), [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference), [GPT 6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [GPT 6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
