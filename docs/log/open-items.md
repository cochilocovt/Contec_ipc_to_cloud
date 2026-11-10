# Open items

Last updated 2026-11-11.

## Where things stand

| Area | State |
|---|---|
| IPC (BX-220) | On the home network and on Tailscale as `ipc` (`100.89.184.100`, key expiry disabled). Windows 10 IoT 1607, last patched December 2016; updates in progress |
| Remote access | Working: Remote Desktop to the IPC over Tailscale (established by 2026-11-09). See [topics/06](topics/06-remote-access.md) |
| Gateway code | Works against the simulator; not yet run on the IPC |
| Client rig | Requirements and design written in [../pump-test-rig/](../pump-test-rig/README.md); nothing built. Needs answers to the client questions first |
| Cloud stack | Tested in the cloud workspace; not yet started on the home PC |
| Simulated PLC on laptop | Not yet set up |
| Backup of the CFast card | Not done yet. Should happen before more changes |

## Next steps, in order

1. Check the Unified Write Filter (`uwfmgr get-config`). If it's on, updates and every other change are thrown away at reboot, so this comes before anything else.
2. Back up the CFast card before the big jump in Windows updates. If there's no USB CFast reader yet, do step 3 first and back up straight after.
3. Finish Windows Update on the IPC until the newest hotfix is 2018 or later, then remove the `AllowEncryptionOracle` workaround on the home PC if it's still set, and check Remote Desktop still connects.
4. Confirm Tailscale "Run unattended" is on, so the IPC stays reachable after reboots.
5. Follow `docs/home-lab-guide.html` from "IPC: Windows housekeeping" onwards.

## Working setup

New sessions should run on Opus 5.5 (lead) with the Haiku workers in `.claude/agents/`. Not yet confirmed in a live session that the workers load and run on Haiku 5.5; check at the start of the next session.

## Waiting on decisions or information

- Client rig answers: [client-questions.md](../pump-test-rig/client-questions.md), especially the servo, the load cell, what "load cell adjustment" means, and target output with tolerance.
- Whether the client's KV-X310 has its OPC UA server enabled, and the ladder program's variables.
- Plant IT: outbound to a cloud hostname on 8883 or 443? A proxy? Or bring our own 4G router? Is Tailscale allowed?
- Production cloud: home-lab stack on a VM, Supabase plus a web host, or AWS IoT / Azure IoT Hub. Free tiers don't fit a commercial client job.
- Extended Security Updates from Contec, or a plan to move off Windows 10 1607 before remote control goes live.
- What the PLC does on heartbeat loss, and whether remote Stop should work in LOCAL mode.
- Whether to build next: the backend and web app with login and a Start/Stop button, and whether on the Docker stack or on Supabase.
