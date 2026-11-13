# Open items

Last updated 2026-11-13 for the client machine-file assessment. Home-lab status below remains from read-only checks at `2026-11-12T09:04:15Z`–`2026-11-12T09:11:25Z`; it was not retested this session.

The full setup remains paused. The owner has temporarily stopped Docker and taken the simulator laptop off the home LAN. Restore the lab only when the owner is ready.

## Where things stand

| Area | Current state |
|---|---|
| IPC cleanup | **Completed successfully.** CBS records maintenance completion with `S_OK` at about `2026-11-11T09:43:42Z`. The task is no longer running; no DISM/TiWorker/WUSA processes were present at the status check. Task Scheduler's result 259 is not the success receipt; the CBS completion record is the evidence |
| IPC Windows | Build remains `14393.2906`. About **13.1 GiB free** (14,087,323,648 bytes); **no pending servicing reboot**. SSU KB5126649 is installed. Baseline KB5062560 and security update KB5126868 are not installed; the baseline MSU is still staged on the IPC |
| IPC startup | Booted at `2026-11-12T04:45:45Z`. Gateway, Tailscale, WinRM and Windows Time are Running/Automatic. Windows logged an unexpected previous shutdown; the cause is not established. This is not a controlled power-restoration/BIOS test |
| IPC housekeeping | Time settings survived reboot; three NTP offsets today were within 0.002 s of the configured Microsoft server. Server SMBv1 remains disabled; its client driver startup is still 2, so full SMBv1 feature/client removal remains pending. Durable control and heartbeat are still disabled |
| Desktop/cloud | Desktop reboot confirmed at `2026-11-12T04:45:51Z`. Docker's Windows service is currently Stopped and no Docker Desktop/backend processes were present, matching the owner's intentional shutdown. The four-service stack and dashboard were not started or retested today |
| Simulator laptop | Currently off the home LAN, per owner. Its automatic simulator service, process recovery and unattended reboot passed on 2026-11-11; current simulator operation is not being claimed |
| Remote access | IPC command access still works. Temporary WinRM/token-policy changes, saved desktop credentials and the temporary laptop setup account still need final cleanup after acceptance |
| CFast image | **Excluded at the owner's request.** No new backup/image will be created. The earlier original-backup confirmation remains owner-reported history |

## Completed and previously tested

- [x] Install/configure the IPC gateway as an automatic NSSM service; test automatic process recovery.
- [x] Install the laptop simulator as an automatic service; test recovery and startup before sign-in.
- [x] Prove the actual laptop → IPC → broker → database → Grafana path (2026-11-11).
- [x] Prove simulator-only Start/Stop, duplicate/expiry/allowlist/TTL/UTC-offset guards, LOCAL-mode refusal and heartbeat-loss stop. Restore durable control/heartbeat to disabled.
- [x] Prove full-minute broker outage/replay without missing sample sequences; retain the ingest persistent-session fix.
- [x] Render all nine dashboard panels and default to `press-01`; record the small negative reading-age observation for later clock-alignment checks.
- [x] Complete IPC component cleanup and recheck free space/reboot state.
- [x] Verify IPC time-sync settings persist after today's reboot. Confirm that the desktop has also restarted.

## Remaining tasks, in order when work resumes

1. [ ] **Finish IPC Windows servicing:** install the staged KB5062560 baseline, then the documented KB5126868 security update with required restarts and service checks. Run a fresh Windows Update scan afterwards; downloaded packages alone are not proof that all applicable updates are installed. Recheck applicability and space before each operation.
2. [ ] **Finish housekeeping:** disable the SMBv1 Windows feature/client; remove the desktop's temporary CredSSP workaround through an administrator action; verify RDP with normal security settings. Open the existing Contec utility once and check for errors without changing watchdog settings.
3. [ ] **Restore the lab when the owner is ready:** return the simulator laptop to the home LAN, check all three LAN addresses, and start Docker/the four cloud services. Verify Docker recovery, fresh three-device data and the dashboard. Investigate desktop/database clock alignment and the previously negative reading age; keep raw timestamps and freshness checks intact meanwhile.
4. [ ] **Complete hands-on acceptance:** physical IPC network-cable loss while the simulator runs, then controlled IPC power-loss/restoration and BIOS automatic-power-on behavior. Prior software heartbeat/reboot tests do not replace these checks.
5. [ ] **Close temporary setup access after acceptance:** remove the laptop setup account, restore local-account token policies and desktop TrustedHosts additions, close lab WinRM rules and delete saved DPAPI credentials. Record final results.

The home lab is not yet declared fully complete. Production cloud choices, plant control approval, ESU enquiries and the client rig remain separate follow-ups below.

## Working setup

- Claude: Opus 5.5 leads, with the Haiku workers in `.claude/agents/`. Both roles completed live CLI smoke tests on 2026-11-11; model-usage metadata reported the selected Opus/Haiku 5.5 identifiers, without independent backend attestation. Both teams now follow [the shared workflow](../agent-workflow.md), with evidence, preflight, bounded output, Windows helpers, executable acceptance, read-only health checks and a lead-owned scorecard. See [topics/09](topics/09-agent-workflow-upgrades.md).
- Codex: GPT 6.1 Sol leads, with `luna_runner` and `luna_scout` on GPT 6 Luna at low reasoning in `.codex/agents/`. The main repository is `cochilocovt/Contec_ipc_to_cloud`; keep authorized project changes and session logs committed and pushed there. Both Codex roles loaded in a fresh CLI session on 2026-11-11; sourced lookup and exact-edit smoke tests passed. Model settings were verified from effective configuration, not independent backend attestation. See [../codex-agents.md](../codex-agents.md) for mapping, limits and validation. Start a fresh chat to load newly added roles; existing chats retain their loaded role list.
- The shared upgrades were tested with both teams. Helper/health unit tests: 18 passed; gateway tests: 18 passed; infrastructure health passed. Three-device telemetry and isolated bench-control acceptance passed on 2026-11-11. IPC/laptop full reboot recovery passed; desktop Docker recovery and physical acceptance remain pending above. The initial [delegation scorecard](delegation-scorecard.jsonl) includes blocked/rejected tasks with causes and explicit measurement limits. Start a fresh Codex chat to load the updated role definitions.

## Waiting on decisions or information

- **ETO & Dose Tester file review (2026-11-13):** [assessment and implementation gaps](../pump-test-rig/machine-file-review-2026-11-13.md). Proposal shows upper force and lower dose measurement; orders specify 100 N/20 N sensors and a two-channel analog amplifier. Confirm installed channel assignment/output range, PLC analog modules and whole-chain accuracy before implementing. Obtain PLC/HMI projects, electrical I/O schedule and approved ETO/dose criteria. Prior single-load-cell proposals need the assessment's force-channel additions. This documentation review did not resume the paused home lab or change machine-control code.

- Client rig answers: [client-questions.md](../pump-test-rig/client-questions.md), especially the servo, the load cell, what "load cell adjustment" means, and target output with tolerance.
- Whether the client's KV-X310 has its OPC UA server enabled, and the ladder program's variables.
- Plant IT: outbound to a cloud hostname on 8883 or 443? A proxy? Or bring our own 4G router? Is Tailscale allowed?
- Production cloud: home-lab stack on a VM, Supabase plus a web host, or AWS IoT / Azure IoT Hub. Free tiers don't fit a commercial client job.
- Extended Security Updates from Contec, or a plan to move off Windows 10 1607 before remote control goes live.
- What the PLC does on heartbeat loss, and whether remote Stop should work in LOCAL mode.
- Whether to build next: the backend and web app with login and a Start/Stop button, and whether on the Docker stack or on Supabase.
