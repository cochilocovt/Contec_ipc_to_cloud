# Three-device home-lab commissioning

## 2026-11-11: access handoff and laptop/cloud checks

The owner asked to finish all three devices from the gateway dependency installation step in `docs/home-lab-guide.html`. The owner reports the IPC dependencies installed and the laptop simulator running on Tailscale. Start-of-session git status was clean and `HEAD` matched fetched `origin/main` (`6bf4af4`). No remote software/configuration changes have been made at this checkpoint.

### Measured state

- Home desktop Tailscale: `100.73.242.65`; home Wi-Fi MQTT binding remains `192.168.1.20:1883`. The broker is not exposed on Tailscale. Grafana stays loopback-only on 3000; project database stays loopback-only on 5433.
- IPC: Tailscale `100.89.184.100`, direct ping through LAN `192.168.1.3`, TCP 3389 open. TCP 22/5985/5986 did not accept connections in the two-second probes. Tailscale connectivity does not supply a command shell.
- Laptop: `mom-laptop`, Tailscale `100.100.157.108`; ping succeeded through DERP. TCP 5020 open; 22/3389/5985/5986 did not accept connections in the two-second probes. Its LAN address and automatic startup are unverified.
- Three direct Modbus read samples returned all seven tags: motor stopped, zero speed/current/count/fault, 25 °C, REMOTE mode. No PLC writes were sent.
- A temporary **home-PC** gateway identified as `home-lab/laptop-check` read the laptop over Tailscale for 12 samples, with control and heartbeat writes disabled. It published 84 rows covering seven metrics through the existing broker/ingest/database. It stopped normally and is offline; its labelled history is retained. This is a laptop/desktop test, **not** proof of the IPC leg.
- Authenticated Grafana checks passed: Timescale datasource health `OK`, provisioned Machine overview dashboard (nine panels), and datasource query returning seven metric rows for `laptop-check`. Passwords were used internally and not printed.
- Existing cloud health check passed. Luna Runner ran 18 gateway tests, 18 helper tests, and quiet Compose validation successfully; result/output hashes and byte sizes were checked by the lead. The lead independently reran the 18 gateway tests.

### One-time command access

The owner chose to have access scripts prepared. Added `tools/enable-lab-remoting.ps1`, `tools/connect-lab-devices.ps1` and [owner instructions](../../lab-remote-access.md).

- Remote bootstrap: Windows PowerShell 5.1, administrator, exact device Tailscale address, firewall required. During setup a block protects ports 5985/5986. Standard broad WinRM rules are disabled; a dedicated service/port/address-scoped rule accepts only this desktop's Tailscale address. Basic authentication and unencrypted WinRM messages are disabled. First-use enabled WinRM rules cause refusal for lead review. A partial setup error leaves the safety block active.
- For workgroup administrator sessions the bootstrap temporarily changes `LocalAccountTokenFilterPolicy`, saving the original value outside the repository. Its `-Disable` closes the lab rule and restores that policy. This policy also affects other Windows remote-administration mechanisms; remove it after commissioning.
- Desktop connection script preserves existing TrustedHosts entries and adds the two exact device addresses. The owner enters existing Windows administrator credentials into local prompts; no passwords go through chat. Verified credentials are saved using Windows DPAPI outside the checkout, under the current user's protected LocalAppData directory, then removed after commissioning.
- Windows PowerShell 5.1 parsed both scripts. The PowerShell test harness passed successful setup ordering/scope, fail-closed behavior, preflight refusal for wrong device/firewall disabled/existing remoting, and original token-policy restoration. Mutating system operations were mocked. Credential-directory ACL construction was checked separately. **Live remote remoting and credential prompts remain untested until the owner runs the scripts.**

References checked 2026-11-11: [Microsoft remoting security](https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/winrm-security?view=powershell-5.1), [PowerShell 5.1 remote troubleshooting](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_remote_troubleshooting?view=powershell-5.1).

### Remaining acceptance

1. Establish authenticated command access; inspect UWF, backup status, patch level, clock, Tailscale unattended state, actual repo/venv/NSSM paths and processes.
2. Inspect/configure the IPC's real gateway config and verify both outgoing connections. Keep durable control/heartbeat settings disabled; any simulator-only command testing must use an explicitly verified isolated bench config and restore disabled control afterwards.
3. Prove the actual laptop → IPC → desktop path with fresh telemetry, correct tag values/timestamps, retained status, and authenticated Grafana queries.
4. Configure and test gateway NSSM and laptop simulator startup/recovery; test broker reconnect/buffering; perform planned device reboot checks when practical. Do not pull power or run Windows updates before UWF/backup prerequisites are understood.
5. Remove temporary access/credentials and update the logs with actual outcomes. Full desktop reboot/sign-in recovery remains untested. Physical PLC/client rig work remains separate and needs plant information/sign-off.

### 2026-11-11: bootstrap file delivery

Rechecked the pending access handoff: TCP 5985/5986 still did not accept connections on either remote device, and neither DPAPI credential file was present on the desktop. IPC RDP and laptop simulator remained reachable. `tailscale file cp --targets` listed both devices; `tailscale file cp --verbose tools/enable-lab-remoting.ps1 ipc:` and the same command targeting `mom-laptop:` each exited 0 and reported the file sent. The owner can receive the script through Tailscale instead of copying it from this checkout. Transfer does not prove receipt into a user folder or execution. No remote configuration, service or PLC setting changed. The required next action remains local execution of the bootstrap and desktop credential prompts.

At `2026-11-11T02:27:30Z`, the third consecutive goal-turn audit still found both devices' TCP 5985/5986 closed/unreachable and both expected credential files absent. There is no verified running setup process to wait on. Commissioning is blocked on owner execution of the already-delivered bootstrap and successful local credential prompts. No additional remote changes or completion claims were made. Resume with fresh access probes and the remaining acceptance steps above after the owner reports both devices connected.
