# Open items

Last updated 2026-11-04.

## Where things stand

| Area | State |
|---|---|
| IPC (BX-220) | On the home network and on Tailscale as `ipc` (`100.89.184.100`, key expiry disabled). Windows 10 IoT 1607, last patched December 2016; updates in progress |
| Remote access | Got as far as the RDP login prompt once; last attempt failed with 0x204 (port 3389 unreachable). See [topics/06](topics/06-remote-access.md) |
| Gateway code | Works against the simulator; not yet run on the IPC |
| Cloud stack | Tested in the cloud workspace; not yet started on the home PC |
| Simulated PLC on laptop | Not yet set up |
| Backup of the CFast card | Not done yet. Should happen before more changes |

## Next steps, in order

1. Get Remote Desktop working again: check `tailscale status` and `Test-NetConnection 100.89.184.100 -Port 3389`; turn on Tailscale "Run unattended" on the IPC.
2. Finish Windows Update on the IPC until the newest hotfix is 2018 or later, then remove the `AllowEncryptionOracle` workaround on the home PC.
3. Check the Unified Write Filter (`uwfmgr get-config`) before relying on any change surviving a reboot.
4. Back up the CFast card. If space runs out, clone onto a 64 GB industrial CFast card and keep the original as the backup.
5. Follow `docs/home-lab-guide.html` from "This PC: start the cloud stack" onwards.

## Waiting on decisions or information

- The final machine's PLC: make, model, and Ethernet or RS-232.
- Plant IT: outbound to a cloud hostname on 8883 or 443? A proxy? Or bring our own 4G router? Is Tailscale allowed?
- Production cloud: home-lab stack on a VM, Supabase plus a web host, or AWS IoT / Azure IoT Hub. Free tiers don't fit a commercial client job.
- Extended Security Updates from Contec, or a plan to move off Windows 10 1607 before remote control goes live.
- Which commands the plant wants, and what the PLC does on heartbeat loss.
- Whether to build next: the backend and web app with login and a Start/Stop button, and whether on the Docker stack or on Supabase.
