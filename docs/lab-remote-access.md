# One-time command access for the home lab

These scripts let the lead finish the three-device setup. They do not start the gateway or change PLC settings. Run them in **Windows PowerShell as administrator** (the blue PowerShell, version 5.1), using the same Windows account that you normally use on each computer.

## 1. IPC and laptop

Copy `tools/enable-lab-remoting.ps1` from this checkout to each device, for example its Desktop. No git, Python installation or repository update is needed to run this script.

On 2026-11-11 the lead also sent this script to both `ipc` and `mom-laptop` using Tailscale file transfer. Receive the file through Tailscale on each device and copy it to the Desktop before running the command below. A successful transfer does not mean the script has run.

On the IPC:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Desktop\enable-lab-remoting.ps1" -Device ipc
```

On the laptop:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Desktop\enable-lab-remoting.ps1" -Device laptop
```

Both must print `READY`. Keep their reported computer/account names for the next step. Stop and report any error; don't disable Windows Firewall or remove a safety block to make it work.

The script enables WinRM on TCP 5985, disables the standard broad WinRM firewall rules, and creates one rule allowing **home-desktop `100.73.242.65` only**, at the device's own Tailscale address. Windows Firewall must already be enabled. A temporary block prevents broad access while setup runs; an error leaves that block active. Existing enabled WinRM rules on first use cause a refusal instead of changing an established management setup.

It disables Basic authentication and unencrypted WinRM messages. Negotiate uses Windows authentication and message encryption, inside the encrypted Tailscale connection. It also temporarily sets `LocalAccountTokenFilterPolicy=1`, allowing local administrators to receive full remote administrator tokens; this policy affects other Windows remote-administration mechanisms too. The original value is saved in `C:\ProgramData\IPC-HomeLab\remoting-state.json` and restored with `-Disable` after commissioning.

## 2. This desktop

Run this on home-desktop in administrator Windows PowerShell **as V.T, the account running Codex**:

```powershell
cd C:\Users\V.T\Documents\ipc_connection
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\connect-lab-devices.ps1
```

Two Windows credential prompts appear, first IPC, then laptop. Use an existing administrator's `COMPUTER\username` and **Windows password**, not the Windows Hello PIN. For the IPC the recorded account is `STANDARD\This pc`; use the actual account shown by the first script if different. A blank-password account cannot be used. Enter passwords only in those prompts, never in chat.

The script adds only the two device IP addresses to WinRM TrustedHosts, preserving existing entries, then verifies a privileged session on each device. It saves DPAPI-encrypted credentials under `%LOCALAPPDATA%\IPC-HomeLab\access`, outside the repository, with directory access limited to the current user and SYSTEM. Only that Windows user on that desktop can decrypt them. The original TrustedHosts value is saved there for cleanup. No password is printed or logged. If one connection fails, only previously successful connections have a saved credential.

When both print `CONNECTED`, tell Codex **access is ready**. The lead can then inspect UWF, clock, updates, paths and processes; configure the IPC; install/start the gateway service; and test the actual three-device path. Tailscale addresses here are verified on 2026-11-11; the MQTT broker remains bound to the home LAN and must not be published to the tailnet or Internet.

If you already pasted the remote script into PowerShell and it printed `READY`, continue with the desktop connection prompts rather than repeating setup. A popup alone does not prove the preceding steps succeeded; the lead still verifies the connections. `-Disable` is a parameter passed when launching the saved script, not a standalone PowerShell command. You can save the original remote script as a `.ps1` file later and use its cleanup command even if setup was originally pasted. Leave access enabled until commissioning is finished; the lead can verify the saved policy snapshot and perform equivalent cleanup remotely.

## Cleanup after commissioning

On each remote device, run its first command again with `-Disable` appended. This closes the lab firewall rule and restores the original local-account token policy. WinRM and its session endpoints remain installed, but the standard WinRM firewall rules stay disabled. It does not restore an unrelated management setup; first-use checks refuse existing enabled WinRM rules for that reason.

On the desktop, in the same administrator account:

```powershell
$accessDir = Join-Path $env:LOCALAPPDATA 'IPC-HomeLab\access'
$oldTrust = [System.IO.File]::ReadAllText((Join-Path $accessDir 'trusted-hosts-before.txt'))
Set-Item WSMan:\localhost\Client\TrustedHosts -Value $oldTrust -Force
Remove-Item -LiteralPath (Join-Path $accessDir 'ipc.credential.xml') -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $accessDir 'laptop.credential.xml') -ErrorAction SilentlyContinue
```

Restore TrustedHosts only if no one has intentionally changed it since setup; otherwise remove just the two lab entries. Keep the non-secret snapshots until cleanup is verified.

References checked 2026-11-11: [Microsoft remoting security](https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/winrm-security?view=powershell-5.1) and [PowerShell 5.1 remote troubleshooting](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_remote_troubleshooting?view=powershell-5.1).
