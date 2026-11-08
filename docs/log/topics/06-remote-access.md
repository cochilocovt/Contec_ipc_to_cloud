# Remote access to the IPC

Goal: work on the IPC from the home PC, and later from anywhere, without opening router ports.

## Setup

- **Tailscale** on the IPC: machine name `ipc`, address `100.89.184.100`, Tailscale 1.104.5, **key expiry disabled** (done 2026-11-04).
- **Remote Desktop** over Tailscale. Windows 10 version 1607 is too old for the built-in OpenSSH server, and Tailscale SSH doesn't run as a server on Windows, so RDP is the way in.
- Windows computer name: `STANDARD`. Account: `This pc`.

Still to do on the IPC: turn on Tailscale **Run unattended** (tray icon → Preferences), so Tailscale runs at the login screen after a reboot. Optionally restrict access to the IPC with Tailscale access rules.

## Problems so far, in order

### 1. Firewall scope

The checklist's `-RemoteAddress LocalSubnet` only allows the home network, not Tailscale addresses. Fix, in an admin PowerShell on the IPC:

```powershell
Set-NetFirewallRule -DisplayGroup "Remote Desktop" -RemoteAddress LocalSubnet,100.64.0.0/10
```

### 2. "An authentication error has occurred. The function requested is not supported" (CredSSP)

Cause: a 2018 Remote Desktop security fix (CredSSP, CVE-2018-0886). Up-to-date PCs refuse to log in to machines without it. The IPC's newest hotfix was **KB3206632, 13 December 2016**.

Proper fix: finish Windows Update on the IPC until the newest `Get-HotFix` entry is 2018 or later.

```powershell
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5
```

Temporary workaround, used on the home PC (admin PowerShell):

```powershell
$p = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\CredSSP\Parameters"
New-Item -Path $p -Force | Out-Null
New-ItemProperty -Path $p -Name AllowEncryptionOracle -PropertyType DWord -Value 2 -Force
```

**Must be undone** once the IPC is patched:

```powershell
Remove-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\CredSSP\Parameters" -Name AllowEncryptionOracle
```

Not used, and not to be used: turning off Network Level Authentication on the IPC.

### 3. Asked for a user name and password

The workaround worked. RDP needs an account on the IPC, not a Tailscale or Microsoft login:
- User name `STANDARD\This pc` (or `.\This pc`).
- The account must have a password: `net user "This pc" *` on the IPC.
- Clear wrong saved credentials on the PC: `cmdkey /delete:TERMSRV/100.89.184.100`.

### 4. Error 0x204: can't connect (open)

The PC couldn't reach port 3389 at all. Likely causes: the IPC restarting or installing updates, or, after setting a password, the IPC waiting at the login screen with Tailscale not running unattended.

Checks from the PC:

```powershell
tailscale status
Test-NetConnection 100.89.184.100 -Port 3389
```

- IPC offline in Tailscale → go to its screen: let updates finish, log in, turn on Run unattended.
- Online but `TcpTestSucceeded : False` → check System Properties → Remote, and `Get-NetFirewallRule -DisplayGroup "Remote Desktop" | Select DisplayName, Enabled, Profile`.

**Status as of 2026-11-04 18:32 IST: unresolved. Resolved by 2026-11-09: Remote Desktop to the IPC works.**

## Updating Windows on the IPC

From December 2016 to current is a big jump:
- Check free space first: around 8–10 GB free on C: is needed; the card is 32 GB (see [topic 03](03-hardware-options.md) for more storage).
- Expect several rounds, often a servicing stack update first.
- A single cumulative update can take an hour or more on the Atom and CFast; don't cut power during "Working on updates".
- If it fails with a 0x8024xxxx or 0x800fxxxx code, install the latest servicing stack update and then the cumulative update by hand from the Microsoft Update Catalog.
