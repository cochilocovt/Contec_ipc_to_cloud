# Open items

Last updated 2026-11-11.

## Where things stand

| Area | State |
|---|---|
| IPC (BX-220) | On the home network and on Tailscale as `ipc` (`100.89.184.100`, key expiry disabled). Windows 10 IoT 1607, last patched December 2016; updates in progress |
| Remote access | Working: Remote Desktop to the IPC over Tailscale (established by 2026-11-09). See [topics/06](topics/06-remote-access.md) |
| Gateway code | Works against the simulator; not yet run on the IPC |
| Client rig | Requirements and design written in [../pump-test-rig/](../pump-test-rig/README.md); nothing built. Needs answers to the client questions first |
| Cloud stack | Running on this PC: MQTT `192.168.1.20:1883`, Grafana `localhost:3000`, project DB `localhost:5433`. Local simulator → gateway → MQTT → DB → Grafana and container restart/data persistence passed; see [topics/08](topics/08-home-pc-setup.md) |
| Simulated PLC on laptop | Not yet set up; spare-laptop LAN address unconfirmed. Temporary local simulator test passed and was stopped |
| Backup of the CFast card | Not done yet. Should happen before more changes |

## Next steps, in order

1. Check the Unified Write Filter (`uwfmgr get-config`). If it's on, updates and every other change are thrown away at reboot, so this comes before anything else.
2. Back up the CFast card before the big jump in Windows updates. If there's no USB CFast reader yet, do step 3 first and back up straight after.
3. Finish Windows Update on the IPC until the newest hotfix is 2018 or later, then remove the `AllowEncryptionOracle` workaround on the home PC if it's still set, and check Remote Desktop still connects.
4. Confirm Tailscale "Run unattended" is on, so the IPC stays reachable after reboots.
5. Set up the spare laptop simulator and the IPC gateway, then verify the three-device path to this PC. Its cloud stack is ready. Current DHCP addresses are sufficient; router reservations are optional. Follow `docs/home-lab-guide.html` from "IPC: Windows housekeeping" onwards.
6. Check this PC after a full reboot/sign-in: Docker should start and `docker compose ps` from `cloud/` should show all four services; this recovery has not been tested.

## Working setup

- Claude: Opus 5.5 leads, with the Haiku workers in `.claude/agents/`. Their live loading/model execution is still unconfirmed.
- Codex: GPT 6.1 Sol leads, with `luna_runner` and `luna_scout` on GPT 6 Luna at low reasoning in `.codex/agents/`. The main repository is `cochilocovt/Contec_ipc_to_cloud`; keep authorized project changes and session logs committed and pushed there. Both Codex roles loaded in a fresh CLI session on 2026-11-11; sourced lookup and exact-edit smoke tests passed. Model settings were verified from effective configuration, not independent backend attestation. See [../codex-agents.md](../codex-agents.md) for mapping, limits and validation. Start a fresh chat to load newly added roles; existing chats retain their loaded role list.

## Waiting on decisions or information

- Client rig answers: [client-questions.md](../pump-test-rig/client-questions.md), especially the servo, the load cell, what "load cell adjustment" means, and target output with tolerance.
- Whether the client's KV-X310 has its OPC UA server enabled, and the ladder program's variables.
- Plant IT: outbound to a cloud hostname on 8883 or 443? A proxy? Or bring our own 4G router? Is Tailscale allowed?
- Production cloud: home-lab stack on a VM, Supabase plus a web host, or AWS IoT / Azure IoT Hub. Free tiers don't fit a commercial client job.
- Extended Security Updates from Contec, or a plan to move off Windows 10 1607 before remote control goes live.
- What the PLC does on heartbeat loss, and whether remote Stop should work in LOCAL mode.
- Whether to build next: the backend and web app with login and a Start/Stop button, and whether on the Docker stack or on Supabase.
