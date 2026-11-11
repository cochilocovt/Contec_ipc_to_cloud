# Open items

Last updated 2026-11-11.

## Where things stand

| Area | State |
|---|---|
| IPC (BX-220) | Restarted at `2026-11-11T05:35:19Z`; registry build `14393.2906`, CBS pending cleared, gateway/Tailscale/WinRM recovered before sign-in. KB5126649 SSU confirmed installed. Built-in component cleanup is running as `IPC-HomeLab-ComponentCleanup` (DISM PID 4648, TiWorker PID 4856 at last observation); monitor that task rather than restarting it |
| Remote access | Administrator WinRM sessions verified on both devices. Laptop uses a temporary `ipc-lab-setup` account; the owner's normal PIN account was not changed. Temporary access/account cleanup remains pending final acceptance. See [topic 10](topics/10-three-device-commissioning.md) |
| Gateway code | Running on the IPC as automatic `ipc-gateway` NSSM service. Python 3.13.17 and pinned dependencies verified; gateway source hashes match this checkout. Durable control/heartbeat writes disabled. Automatic process recovery and fresh telemetry passed |
| Client rig | Requirements and design written in [../pump-test-rig/](../pump-test-rig/README.md); nothing built. Needs answers to the client questions first |
| Cloud stack | Running: MQTT `192.168.1.20:1883`, Grafana `localhost:3000`, project DB `localhost:5433`. Actual laptop → IPC → DB → authenticated Grafana query passed. Ingest now keeps a persistent MQTT session; a full-minute broker outage replayed all samples without sequence gaps. See [topic 10](topics/10-three-device-commissioning.md) |
| Simulated PLC on laptop | Rebooted at `2026-11-11T05:49:05Z`; simulator/Tailscale/WinRM and LAN listener recovered before sign-in, with the same `.10` address. Automatic NSSM `ipc-simulator`, REMOTE mode, 6 s timeout. Bench command/guard/heartbeat tests passed; restored stopped/fault 0. Permanent gateway remains read-only |
| Backup of the CFast card | Owner earlier reported a verified original backup; its artifact was not inspected. Owner has now explicitly excluded the final updated-card backup from this setup. No new image will be created |

## Next steps, in order

1. **Monitor the running IPC component cleanup, then finish applicable Windows updates.** Both remote reboot tests passed before sign-in. The original IPC monitor `40380` ended on an obsolete remote shell; a fresh session proved the reboot. Do not rerun that restart. Official SSU KB5126649 is already installed; July 2025 baseline KB5062560 is the documented prerequisite for October 2026 security update KB5126868. Verified x64 LTSB installers are staged on this desktop under ignored `logs/vendor/windows-updates/`. Await cleanup completion and recheck free space before installation; remove the home-PC CredSSP workaround through a reviewed administrator action.
2. Test this PC after reboot/sign-in (Docker start and all four services). IPC and laptop full reboot recovery are verified, including Tailscale and data services before sign-in; this desktop's full reboot/sign-in is still untested.
3. Complete the guide's physical cable-loss and power-loss checks. The software heartbeat-loss test passed; it is not evidence of physical cable removal or BIOS power-loss recovery. The owner has explicitly excluded the finished-card image from the remaining scope.
4. Remove temporary WinRM access, restore the saved local-account token policy and desktop TrustedHosts changes, delete saved DPAPI credentials, and remove the temporary laptop account. Update the final commissioning record. The complete setup is not yet claimed.

## Working setup

- Claude: Opus 5.5 leads, with the Haiku workers in `.claude/agents/`. Both roles completed live CLI smoke tests on 2026-11-11; model-usage metadata reported the selected Opus/Haiku 5.5 identifiers, without independent backend attestation. Both teams now follow [the shared workflow](../agent-workflow.md), with evidence, preflight, bounded output, Windows helpers, executable acceptance, read-only health checks and a lead-owned scorecard. See [topics/09](topics/09-agent-workflow-upgrades.md).
- Codex: GPT 6.1 Sol leads, with `luna_runner` and `luna_scout` on GPT 6 Luna at low reasoning in `.codex/agents/`. The main repository is `cochilocovt/Contec_ipc_to_cloud`; keep authorized project changes and session logs committed and pushed there. Both Codex roles loaded in a fresh CLI session on 2026-11-11; sourced lookup and exact-edit smoke tests passed. Model settings were verified from effective configuration, not independent backend attestation. See [../codex-agents.md](../codex-agents.md) for mapping, limits and validation. Start a fresh chat to load newly added roles; existing chats retain their loaded role list.
- The shared upgrades were tested with both teams. Helper/health unit tests: 18 passed; gateway tests: 18 passed; infrastructure health passed. Actual three-device telemetry and isolated bench-control acceptance now pass; full-device reboot/physical acceptance remains pending above. The initial [delegation scorecard](delegation-scorecard.jsonl) includes blocked/rejected tasks with causes and explicit measurement limits. Start a fresh Codex chat to load the updated role definitions.

## Waiting on decisions or information

- Client rig answers: [client-questions.md](../pump-test-rig/client-questions.md), especially the servo, the load cell, what "load cell adjustment" means, and target output with tolerance.
- Whether the client's KV-X310 has its OPC UA server enabled, and the ladder program's variables.
- Plant IT: outbound to a cloud hostname on 8883 or 443? A proxy? Or bring our own 4G router? Is Tailscale allowed?
- Production cloud: home-lab stack on a VM, Supabase plus a web host, or AWS IoT / Azure IoT Hub. Free tiers don't fit a commercial client job.
- Extended Security Updates from Contec, or a plan to move off Windows 10 1607 before remote control goes live.
- What the PLC does on heartbeat loss, and whether remote Stop should work in LOCAL mode.
- Whether to build next: the backend and web app with login and a Start/Stop button, and whether on the Docker stack or on Supabase.
