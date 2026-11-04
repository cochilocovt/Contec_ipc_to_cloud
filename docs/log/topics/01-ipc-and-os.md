# The IPC and its operating system

## Can the BX-220 do this job? (2026-10-31)

Yes, as an edge gateway. It does not display anything "on the cloud" itself: it reads the machine's PLC, pushes the data to a cloud broker, and the dashboard lives in the cloud. It can keep driving a local screen at the same time.

Why it suits the job:
- Atom E3845 quad-core, 4 GB ECC RAM, fanless.
- Two gigabit LAN ports: one for the PLC network, one for the internet, with nothing routed between them.
- Two RS-232C ports, for PLCs that use serial.
- Contec's RAS feature restarts the box on a program hang, a failed boot or overheating, and keeps a fault log.
- Contec marketed the series for IoT gateways, industrial control and signage.

Limits: fine for collecting and forwarding data, not for hosting the database or dashboards on the box. CFast flash wears with heavy writing.

Typical chain proposed: PLC → (Modbus TCP/RTU, OPC UA or serial) → collector on the BX-220 → MQTT over TLS → cloud broker → time-series database → dashboard.

## The operating system

- Shipped with Windows 10 IoT Enterprise 2016 LTSB, 64-bit (version 1607).
- **Support ended 2026-10-13**; that was the last monthly security update. Extended Security Updates for this edition are sold only through device makers, so through Contec.
- When checked on 2026-11-04, the newest hotfix installed was **KB3206632 (13 December 2016, build 14393.576)**: almost ten years behind. This caused the Remote Desktop CredSSP error ([topic 06](06-remote-access.md)).
- The box may run the **Unified Write Filter**. If it's on, every change, including Windows updates, is discarded at reboot. Check with `uwfmgr get-config`.

## Linux or Windows? (2026-10-31)

The first checklist proposed replacing Windows with Debian 13, mainly because of the end of support. The owner chose to **keep Windows**. Consequences, recorded in [../../decisions.md](../../decisions.md):
- No patches unless ESUs are bought; keep it behind a deny-all inbound firewall.
- The Unified Write Filter must be managed (off for setup, on with exclusions at the end).
- Contec's RAS utility is Windows-only, so it stays available.
- The gateway runs as a Windows service under NSSM.
- Settle ESUs or a migration date before remote control goes live at the plant.

## Setup on the IPC

The full list is in `docs/home-lab-guide.html` and `docs/bx220-setup-checklist.html`. The order agreed on 2026-11-03:
1. Record first, change nothing: UWF status, `winver`, `systeminfo`, `ipconfig /all`, startup items, services, installed programs, COM ports, network adapters, accounts.
2. Back up the CFast card (image on the home PC with a USB CFast reader, verify by booting a copy, keep two copies).
3. Fixed IP or DHCP reservation, Remote Desktop for the LAN (later via Tailscale), no sleep or hibernation, Windows Update to the end, internet time.
4. Python 3.12 64-bit and the project folder.

There's no HMI at home, so the HMI recording steps were dropped.

The Windows account on the IPC is `This pc`; the computer name is `STANDARD`.
