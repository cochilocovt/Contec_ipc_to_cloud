# Open items

Last updated 2026-11-11.

## Where things stand

| Area | State |
|---|---|
| IPC (BX-220) | On the home network and on Tailscale as `ipc` (`100.89.184.100`, key expiry disabled). Windows 10 IoT 1607, last patched December 2016; updates in progress |
| Remote access | Working: Remote Desktop to the IPC over Tailscale (established by 2026-11-09). See [topics/06](topics/06-remote-access.md) |
| Gateway code | Owner reports dependencies installed on the IPC. Both remote bootstraps now report READY and TCP 5985 accepts connections; desktop credential verification is pending. Gateway not yet run there |
| Client rig | Requirements and design written in [../pump-test-rig/](../pump-test-rig/README.md); nothing built. Needs answers to the client questions first |
| Cloud stack | Running on this PC: MQTT `192.168.1.20:1883`, Grafana `localhost:3000`, project DB `localhost:5433`. Local simulator → gateway → MQTT → DB → Grafana and container restart/data persistence passed; see [topics/08](topics/08-home-pc-setup.md) |
| Simulated PLC on laptop | Running on `mom-laptop`, Tailscale `100.100.157.108:5020`. Read-only Modbus reads and laptop → temporary home-PC gateway → DB → authenticated Grafana query passed. Laptop startup/reboot and IPC → laptop path still untested |
| Backup of the CFast card | Not done yet. Should happen before more changes |

## Next steps, in order

0. **Awaiting desktop credential verification.** The owner reports both remote scripts now print READY (their contents were pasted into administrator PowerShell). At `2026-11-11T04:04:34Z`, TCP 5985 accepted connections on both devices, but both desktop credential files were still absent. Finish the two prompts in [one-time command access](../lab-remote-access.md): first the IPC administrator account, then the laptop administrator account, using Windows passwords rather than PINs. See [topic 10](topics/10-three-device-commissioning.md). Three-device completion is not claimed; proceed after both desktop connection checks succeed.
1. Check the Unified Write Filter (`uwfmgr get-config`). If it's on, updates and every other change are thrown away at reboot, so this comes before anything else.
2. Back up the CFast card before the big jump in Windows updates. If there's no USB CFast reader yet, do step 3 first and back up straight after.
3. Finish Windows Update on the IPC until the newest hotfix is 2018 or later, then remove the `AllowEncryptionOracle` workaround on the home PC if it's still set, and check Remote Desktop still connects.
4. Confirm Tailscale "Run unattended" is on, so the IPC stays reachable after reboots.
5. Inspect the existing laptop simulator setup and configure the IPC gateway, then verify the three-device path to this PC. Its cloud stack is ready. Current DHCP addresses are sufficient; router reservations are optional. Follow `docs/home-lab-guide.html` from "IPC: Windows housekeeping" onwards. Keep the MQTT broker on the home LAN; the laptop simulator is currently reachable over Tailscale. Finish with NSSM startup/recovery, simulator startup/recovery, and removal of temporary management access/credentials.
6. Check this PC after a full reboot/sign-in: Docker should start and `docker compose ps` from `cloud/` should show all four services; this recovery has not been tested.

## Working setup

- Claude: Opus 5.5 leads, with the Haiku workers in `.claude/agents/`. Both roles completed live CLI smoke tests on 2026-11-11; model-usage metadata reported the selected Opus/Haiku 5.5 identifiers, without independent backend attestation. Both teams now follow [the shared workflow](../agent-workflow.md), with evidence, preflight, bounded output, Windows helpers, executable acceptance, read-only health checks and a lead-owned scorecard. See [topics/09](topics/09-agent-workflow-upgrades.md).
- Codex: GPT 6.1 Sol leads, with `luna_runner` and `luna_scout` on GPT 6 Luna at low reasoning in `.codex/agents/`. The main repository is `cochilocovt/Contec_ipc_to_cloud`; keep authorized project changes and session logs committed and pushed there. Both Codex roles loaded in a fresh CLI session on 2026-11-11; sourced lookup and exact-edit smoke tests passed. Model settings were verified from effective configuration, not independent backend attestation. See [../codex-agents.md](../codex-agents.md) for mapping, limits and validation. Start a fresh chat to load newly added roles; existing chats retain their loaded role list.
- The shared upgrades were tested with both teams. Final helper/health unit tests: 18 passed; gateway tests: 18 passed; infrastructure health passed. Full device-path/reboot checks remain pending above. The initial [delegation scorecard](delegation-scorecard.jsonl) includes blocked/rejected tasks with causes and explicit measurement limits. Start a fresh Codex chat to load the updated role definitions.

## Waiting on decisions or information

- Client rig answers: [client-questions.md](../pump-test-rig/client-questions.md), especially the servo, the load cell, what "load cell adjustment" means, and target output with tolerance.
- Whether the client's KV-X310 has its OPC UA server enabled, and the ladder program's variables.
- Plant IT: outbound to a cloud hostname on 8883 or 443? A proxy? Or bring our own 4G router? Is Tailscale allowed?
- Production cloud: home-lab stack on a VM, Supabase plus a web host, or AWS IoT / Azure IoT Hub. Free tiers don't fit a commercial client job.
- Extended Security Updates from Contec, or a plan to move off Windows 10 1607 before remote control goes live.
- What the PLC does on heartbeat loss, and whether remote Stop should work in LOCAL mode.
- Whether to build next: the backend and web app with login and a Start/Stop button, and whether on the Docker stack or on Supabase.
