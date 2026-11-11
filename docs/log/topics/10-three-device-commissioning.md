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

### Original acceptance plan at the access checkpoint

1. Establish authenticated command access; inspect UWF, backup status, patch level, clock, Tailscale unattended state, actual repo/venv/NSSM paths and processes.
2. Inspect/configure the IPC's real gateway config and verify both outgoing connections. Keep durable control/heartbeat settings disabled; any simulator-only command testing must use an explicitly verified isolated bench config and restore disabled control afterwards.
3. Prove the actual laptop → IPC → desktop path with fresh telemetry, correct tag values/timestamps, retained status, and authenticated Grafana queries.
4. Configure and test gateway NSSM and laptop simulator startup/recovery; test broker reconnect/buffering; perform planned device reboot checks when practical. Do not pull power or run Windows updates before UWF/backup prerequisites are understood.
5. Remove temporary access/credentials and update the logs with actual outcomes. Full desktop reboot/sign-in recovery remains untested. Physical PLC/client rig work remains separate and needs plant information/sign-off.

### 2026-11-11: bootstrap file delivery

Rechecked the pending access handoff: TCP 5985/5986 still did not accept connections on either remote device, and neither DPAPI credential file was present on the desktop. IPC RDP and laptop simulator remained reachable. `tailscale file cp --targets` listed both devices; `tailscale file cp --verbose tools/enable-lab-remoting.ps1 ipc:` and the same command targeting `mom-laptop:` each exited 0 and reported the file sent. The owner can receive the script through Tailscale instead of copying it from this checkout. Transfer does not prove receipt into a user folder or execution. No remote configuration, service or PLC setting changed. The required next action remains local execution of the bootstrap and desktop credential prompts.

At `2026-11-11T02:27:30Z`, the third consecutive goal-turn audit still found both devices' TCP 5985/5986 closed/unreachable and both expected credential files absent. There is no verified running setup process to wait on. Commissioning is blocked on owner execution of the already-delivered bootstrap and successful local credential prompts. No additional remote changes or completion claims were made. Resume with fresh access probes and the remaining acceptance steps above after the owner reports both devices connected.

### 2026-11-11: both remote bootstraps report READY

The owner clarified that the script contents were pasted into PowerShell rather than invoked as saved files, then reported READY on both devices. At `2026-11-11T04:04:34Z`, independent TCP probes succeeded on port 5985 at both device addresses. Neither desktop credential file was present, so authenticated session checks and remote configuration inspection remain pending. Explained that the desktop prompts use the IPC administrator account first (recorded as `STANDARD\This pc`) and the laptop administrator account second; `whoami` in the laptop's administrator PowerShell supplies its account name. Passwords are the target Windows account passwords, not the desktop's password or a Windows Hello PIN. Explained that cleanup can use the saved script or equivalent remote operations after verifying the policy snapshot; no cleanup was executed.

### 2026-11-11: actual IPC service and three-device telemetry

The desktop's IPC credential appeared and an administrator WinRM session succeeded. No password was printed. Read-only IPC checks established:

- Computer `STANDARD`, Windows 10 Enterprise 2016 LTSB, build 14393. Reported hotfixes included KB3206632, KB4049411 and KB4033631. A CBS servicing reboot is pending. C: had 5,475,004,416 bytes free (about 5.1 GiB). No OS update or reboot was attempted; a verified CFast backup remains unrecorded.
- UWF current/next session OFF and servicing OFF; no protected volumes configured. The utility emitted UTF-16 text through remoting, so its output contained embedded NULs, but the OFF states were readable.
- Tailscale/WinRM services running automatically. Tailscale preferences: `ForceDaemon=true`, `WantRunning=true`, `LoggedOut=false`. LAN `192.168.1.3`. The lab WinRM firewall address filter is exactly local `100.89.184.100`, remote `100.73.242.65`; no standard WINRM rule was enabled. The saved policy snapshot exists and records no original `LocalAccountTokenFilterPolicy` value.
- `C:\ipc_connection\gateway\.venv` runs Python 3.13.17 x64 with pymodbus 3.11.4, paho-mqtt 2.1.0 and PyYAML 6.0.3. SHA-256 hashes of all six gateway modules, requirements and the example config matched this checkout.
- IPC TCP connections to laptop `100.100.157.108:5020` and home broker `192.168.1.20:1883` succeeded. The real config was absent, so it was created exclusively from the example with only those two hosts changed; both durable control and heartbeat writes remain disabled.

A supervised 20-sample IPC run stored 140 metric rows and passed live freshness/online checks. Its final stderr warning caused PowerShell's native-command error handling to terminate the shell pipeline; a separate five-sample foreground run with file logging completed and asserted successfully. This was a launcher issue, not a gateway/PLC read failure.

Installed `ipc-gateway` using NSSM build `2.24-101-g897c7ad` win64 from the [vendor download](https://nssm.cc/download), checked 2026-11-11. Binary is at `C:\ProgramData\IPC-HomeLab\nssm\nssm.exe`; SHA-256 `eee9c44c29c2be011f1f1e43bb8c3fca888cb81053022ec5a0060035de16d848`. Downloaded ZIP SHA-256 `99f5045fffbffb745d67fe3a065a953c4a3d9c253b868892d9b685b0ee7d07b8`; 415,458 ZIP bytes and 368,640 binary bytes. Ignored local provenance is in `logs/vendor/`.

Service settings: automatic startup, LocalSystem, application `C:\ipc_connection\gateway\.venv\Scripts\python.exe`, working directory `C:\ipc_connection\gateway`, parameters `-m ipc_gateway --config config\gateway.yaml --log-file logs\gateway.log`. NSSM restarts exits after 5 seconds; SCM recovery also restarts wrapper failures. The gateway log rotates at 2 MB with five backups; redirected service stdout/stderr use NSSM online rotation at 2 MB. Killing only the verified gateway process tree under NSSM changed its root PID from 2752 to 1200 in 5.95 seconds; a follow-up confirmed service Running and fresh online telemetry. No Windows reboot was performed.

The read-only configuration also rejected test Start command `03793dbb-6af0-4082-a9cd-494d8557cad3` with `control is disabled on this gateway`. Both MQTT acknowledgement and database audit row were checked; the simulator remained stopped. Non-secret command evidence is under `logs/agent-runs/20261111-ipc-control-disabled/`.

### Broker replay defect found and fixed

The first 20-second broker outage lost 30 samples: broker logs showed the gateway reconnecting about a second before ingest's clean-session connection, so replay occurred before any ingest subscription existed. The missing sequence range remains historical test data; it was not fabricated or backfilled. Evidence: `logs/agent-runs/20261111-ipc-broker-buffer/result.json`.

Changed only ingest's MQTT constructor to `clean_session=False`, retaining its existing fixed `ingest` client ID and broker persistence volume. Rebuilt/recreated ingest without changing credentials or volumes; broker logs confirmed `c0`. [Paho documentation](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html) confirms that this retains subscriptions and queued messages across disconnects. No PLC command rule, tag, schema or payload changed.

- Repeated 20-second outage: 32 samples, all seven metrics, zero missing sequences, maximum timestamp interval 1.062 s. Evidence: `logs/agent-runs/20261111-ipc-broker-buffer-retest/result.json`.
- Full-minute outage: broker stopped at `2026-11-11T04:19:41.430Z`, started at `04:20:41.871Z`. Across the entire baseline/reconnect window, 93 samples arrived with all seven metrics, zero missing sequences and maximum interval 1.081 s. Evidence: `logs/agent-runs/20261111-ipc-broker-buffer-minute/result.json`.
- Authenticated Grafana checks at `2026-11-11T04:22:51Z`: datasource `OK`, Machine overview dashboard with nine panels, `press-01` online, all seven latest metrics returned through the Grafana datasource, maximum age 1.596 s. Evidence: `logs/agent-runs/20261111-ipc-grafana/result.json`. Open `http://localhost:3000/d/ipc-machine?var-machine=press-01` on this desktop.

### Still waiting on the laptop login and remaining acceptance

The owner only knows the laptop PIN. Supplied a separate temporary local administrator account approach, preserving the owner's normal account/password. After `-AsSecureString` was treated as a standalone command, clarified that the complete `Read-Host` command must run first, password entry must finish, and only then should the account commands be pasted. No password is recorded. Laptop authentication, simulator service/startup, isolated bench command tests, full-device reboot checks and temporary-account/access cleanup remain unfinished. The durable gateway stays read-only and is already running on the IPC.

### 2026-11-11: laptop service and LAN data path

The laptop credential subsequently appeared, and an administrator session using the temporary `ipc-lab-setup` account succeeded. Computer `DESKTOP-RJOJQ4V`, Windows 11 Home Single Language 10.0.26200, LAN `192.168.1.10`. Repository `C:\ipc_connection`; simulator and requirements hashes matched this checkout. Its virtual environment runs Python 3.15.2 x64 with the same pinned pymodbus/paho/PyYAML versions. The original manual `run-sim.bat` instance had one venv root process and one base-Python child, listening on all interfaces.

Tailscale private-preference lookup through that temporary account returned `401 Unauthorized: Tailscale already in use` by the normal laptop user. Reported it and did not switch identities or bypass that restriction. The owner reports enabling Run unattended from the normal login; one verification attempt after that external change still returned 401. Windows service startup is automatic, but actual post-reboot Tailscale reachability is not yet proved.

Confirmed that IPC reads work through laptop LAN `192.168.1.10:5020`. Set that trusted home Wi-Fi network to Private and added project rule `IPC-HomeLab-SimPLC` for TCP 5020, local `.10`, remote IPC `.3`, Wi-Fi/Private. Existing application firewall allowances were not removed. Installed automatic LocalSystem NSSM `ipc-simulator` with the same verified binary, working directory `C:\ipc_connection`, parameters `C:\ipc_connection\tools\sim_plc.py --host 192.168.1.10 --port 5020 --mode remote --heartbeat-timeout 6`, 5 s restart delay, SCM wrapper recovery and rotating stdout/stderr under root `logs/`.

Stopped only the verified manual simulator process tree after configuring its replacement. The service started and listens specifically on the LAN address, no longer on the Tailscale address. Changed the IPC's real PLC host to `192.168.1.10`, preserving its MQTT host and disabled control/heartbeat. The prior config is in ignored IPC `gateway\logs\gateway-before-lan-20261111T043034Z.yaml`. Restarted the gateway service and verified fresh telemetry. Killing only the verified simulator process tree under NSSM changed its root PID 11180 → 3988; service Running and new listener were observed after 7.11 s. No Windows reboot occurred. Laptop AC sleep and AC hibernate were already Never, and AC power was connected; battery settings were not changed.

### 2026-11-11: isolated three-device command acceptance

Lead-owned live controller and full evidence are under ignored `logs/agent-runs/20261111-bench-control/` (`check.py`, `result.json`, `mqtt-events.json`, server/management output). The temporary IPC gateway loaded the durable read-only config, asserted its simulator LAN target and allowlist, then enabled control/heartbeat **in memory only** under `home-lab/control-check` with a distinct MQTT client ID and a 240 s watchdog. It did not change the durable config, tag map, allowlist or PLC authority. Commands originated from this desktop and traversed its broker to the IPC and laptop simulator.

- Start and Stop each returned accepted → executed; subsequent telemetry confirmed running → stopped.
- Reusing the first Start's ID was rejected as a duplicate. That ID had exactly one executed acknowledgement, and fresh telemetry remained stopped after the duplicate. The commands table's latest status for that ID is rejected, while its event history retains the original execution and later duplicate rejection.
- Already-expired, unknown `write_anything`, more-than-30-second TTL and missing-UTC-offset commands were refused with the expected reasons. The invalid-offset request is intentionally absent from the commands table; its rejection event was recorded.
- Restarted only the simulator service in LOCAL mode: telemetry showed LOCAL and Start was rejected as `machine in LOCAL mode`. Restored REMOTE mode afterwards.
- Started once more, stopped the temporary gateway, and observed the simulator stop with fault 9 through the permanent gateway's telemetry. Observation took 7.531 s from initiating remote stop, including remote-call and one-second telemetry delay; this is not a direct six-second physical stop-time measurement. Simulator timeout is configured as 6 s. This tests heartbeat loss, not physical cable removal.
- The temporary gateway exited 0. Restarted the simulator in REMOTE mode and independently observed motor stopped, speed/current/count 0, temperature 25 °C and fault 0. Verified both permanent services Running and the real IPC config still has `control.enabled=false` and heartbeat disabled.

Current remaining acceptance is in `open-items.md`: CFast backup/servicing prerequisites, full-device reboot/sign-in, physical cable/power-loss checks and finished-card image, followed by temporary access/account cleanup. The owner has been asked for the CFast backup status. Software services and command-path tests are complete; the whole project is not yet declared complete.

The owner subsequently confirmed that a verified CFast backup exists. This is owner-reported evidence; the image itself was not inspected. Preparing a normal IPC restart to finish pending servicing and test automatic recovery, with build/space review before further updates.

During source review, origin had two additive owner helper commits (`6843ad4`, `249ae1a`) creating `sentence1` and `sentence2`. Preserved all eight lead-owned changed files in ignored backups and a named stash, fast-forwarded the clean branch, restored and verified the owned files byte-for-byte, then dropped only the verified task stash. The two owner files were preserved without edits. Reconciliation evidence is under `logs/agent-runs/20261111-git-reconcile/`.
