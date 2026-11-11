# Timeline

Times are India time (IST). Each entry: what was asked, the short answer, and what changed in the repo.

## 2026-10-31 (Saturday)

**Can the Contec BX-220D-DC781724 show machine performance on the cloud?**
Yes, as an edge gateway: it reads the PLC and pushes data to a cloud broker, and the dashboard lives in the cloud. The hardware suits the job (Atom E3845, 4 GB, two LAN ports, two RS-232). Flagged that its OS, Windows 10 IoT Enterprise 2016 LTSB, reached end of support on 2026-10-13. → [topics/01](topics/01-ipc-and-os.md)

**What changes if the client also wants to start and stop a motor remotely? What would the data look like on a Raspberry Pi?**
Designed the write path: the cloud only requests and the PLC decides; allowlisted commands only; every command has an id and short expiry; confirm by telemetry; heartbeat for link loss; hardwired E-stop. Defined the MQTT topics, telemetry, command and ack payloads, and the tag map. The data is identical on a Pi; only the tag map is hardware-specific. Don't drive motors from bare Pi GPIO. → [topics/02](topics/02-remote-control.md), [../data-contract.md](../data-contract.md)

**Other low-cost, factory-approved edge devices instead of a Pi?**
Compared Seeed reComputer R1000, Revolution Pi Connect 5, Siemens IOT2050, Moxa UC-1200A, Teltonika TRB145/TRB140 and Arduino Opta, with Indian prices where available. → [topics/03](topics/03-hardware-options.md)

**Which Raspberry Pi for a POC, bought in India?**
Raspberry Pi 5, 2 GB, from an approved reseller (Robu.in, Robocraze, Silverline). Prices had risen several times in 2026 because of memory costs. → [topics/03](topics/03-hardware-options.md)

**Can a spare Samsung 8 GB DDR4 laptop stick be used with a Pi?**
No: Pi memory is soldered on, and the BX-220 uses DDR3L. Useful in a DDR4 mini PC or thin client, or sell it. → [topics/03](topics/03-hardware-options.md)

**IPC in hand: build a setup task list.**
First built a Linux-based checklist; changed to keep Windows at the owner's request. Published the checklist (later `docs/bx220-setup-checklist.html`). Key Windows items: Unified Write Filter, Contec RAS utility, COM port ownership, no patches since October 2026. → [topics/01](topics/01-ipc-and-os.md)

## 2026-11-03 (Tuesday)

**Turn this chat into a project in `C:\Users\V.T\Documents\ipc_connection`.**
Created the git repo: Python gateway (Modbus polling, MQTT telemetry, offline buffer, allowlisted commands with expiry and dedupe, heartbeat), simulated PLC, command sender, unit tests, and docs (architecture, data contract, hardware, decisions, checklist), plus `CLAUDE.md`. Tested end to end in the cloud workspace. Commit `c6ff015`.

**IPC booted and on the home network: what to do on it?**
Record first (Unified Write Filter status, winver, ipconfig, startup items, COM ports, accounts), then back up the CFast card, then updates, RDP, power settings, time sync, Python. → [open-items.md](open-items.md)

## 2026-11-04 (Wednesday)

**No HMI at home. A Keyence KV-8000 is available, but the final machine uses a different PLC. Use it, or emulate on a spare laptop?**
Emulate on the laptop for day-to-day work. Give the KV-8000 one limited session: a second protocol (Keyence Host Link, port 8501; Modbus TCP support unconfirmed), real network behaviour, and practising the Local/Remote and heartbeat ladder logic. → [topics/03](topics/03-hardware-options.md)

**Continue the setup while the IPC updates.**
Built the home-lab cloud stack in `cloud/` (Mosquitto, TimescaleDB, ingest service, Grafana with a "Machine overview" dashboard and read-only database login), `tools/run-sim.bat` and `docs/home-lab.md`. Tested end to end with Docker, including commands, gateway crash and heartbeat fault. Commit `b62078c`.

**Create an explanatory web page: which task on which device, with an offline checklist.**
Built `docs/home-lab-guide.html` with the web-artifacts-builder skill: device roles, connection diagram, read and write flows, 50-task checklist tagged by device, IP fields that fill into commands, ticks saved in the browser. Published as an artifact too. Commits `571656b`, `ff45d57`.

**On a real shop floor, does the edge device post straight to the cloud?**
Usually yes, but through the plant firewall, its own 4G router, or an on-site server that forwards to the cloud. The gateway works with all three unchanged. Remote control is where plants push back. → [topics/04](topics/04-plant-connectivity.md)

**How does a client use a start/stop button on the dashboard?**
Through a web app with its own backend, never browser-to-MQTT. Login and roles, state-aware button, confirmation, backend fills `issued_by`, live status through to "confirmed" by telemetry, audit log. Grafana stays for viewing. → [topics/02](topics/02-remote-control.md)

**Can the cloud side use free Supabase and Vercel instead?**
Supabase covers the database, logins and live updates; neither hosts an MQTT broker or an always-on ingest. Proposed variant: the gateway talks to Supabase directly over HTTPS and Realtime. Catches: Vercel Hobby is non-commercial only; Supabase free is 500 MB and pauses after a week idle; the current table design would fill 500 MB in about a week. → [topics/05](topics/05-cloud-hosting.md)

**Remote access to the IPC (Tailscale installed).**
RDP over Tailscale (`100.89.184.100`, Windows name `STANDARD`, account `This pc`). Fixed in order: firewall scope for Tailscale addresses; CredSSP error because the IPC was last patched in December 2016 (KB3206632) and needs updates, with a temporary client-side workaround; credentials format. Last state: error 0x204, the IPC not reachable on 3389, likely restarting for updates or Tailscale not running unattended. → [topics/06](topics/06-remote-access.md)

**Can the IPC's storage be increased? Why are CFast cards expensive?**
Yes: clone to a larger industrial CFast (64 GB is enough), or use the second slot for data, or free space on the 32 GB card. CFast is an SSD in card form, made in low volume for cinema cameras and industrial PCs, with industrial-grade flash on top. → [topics/03](topics/03-hardware-options.md)

**Push the project to GitHub and keep a log of everything discussed.**
Added this log and pushed the repo, with history, to `github.com/cochilocovt/Contec_ipc_to_cloud`.

## 2026-11-05 (Thursday)

**The client machine: a pump volumetric test rig on a Keyence KV-X310. Remote control of a servo (adjustment), the load cell (adjustment) and start/stop, plus analytics. Document it separately from the home lab.**
Wrote `docs/pump-test-rig/`: overview, KV-X310 notes, remote control, data and analytics, and questions for the client. Main points: the KV-X310's built-in port has a confirmed OPC UA server but Modbus TCP is confirmed only on the KV-XLE02 add-on, so the gateway needs a new driver (OPC UA proposed, Host Link as fallback); the PLC should measure each stroke and buffer the results rather than relying on 1 s polls; setpoints need value-carrying commands with limits checked in three places; setpoints change only while idle; output measured by weight, with an early check that the load cell can resolve a single stroke. Home-lab files unchanged. → [topics/07](topics/07-pump-test-rig.md)

**Where would Node-RED fit if we went that route?**
On the BX-220, in place of the Python gateway: PLC reads, telemetry and stroke records out, commands in. The cloud side is unchanged because the data contract is the same. Easier: ready-made OPC UA, Modbus and Keyence Host Link nodes, fast changes, and plant staff can edit flows. Harder: the write-path rules would move from tested Python into function nodes; flows diff poorly in git; the offline buffer and saved results index must be built by hand; Node.js on Windows 10 1607 is untested. Not a fit for the client control UI or as a safety layer. Suggested: use it now as a bench tool to explore the KV-X310, keep the Python gateway for production unless the client's own staff will maintain the edge. → [topics/07](topics/07-pump-test-rig.md)

## 2026-11-09 (Monday)

**Repo is on GitHub and cloned on another Windows PC; Remote Desktop to the IPC now works. What are the next three tasks?**
1. Check the Unified Write Filter. 2. Back up the CFast card. 3. Finish Windows Update and remove the CredSSP workaround. Order changed from the earlier list: the write-filter check moves first because it decides whether updates survive a reboot, and the backup moves before the updates because a ten-year jump in updates on 1607 can fail. Updated `open-items.md` and topic 06.

## 2026-11-10 (Tuesday)

**All three home-lab machines run Tailscale. Tailscale or local addresses in the guide?**
IPC_IP (used only for Remote Desktop): Tailscale address. LAPTOP_IP and PC_IP (gateway to PLC and broker): local addresses, because that matches the plant (the real PLC can't run Tailscale) and the guide's Private-profile firewall rules. Reserve the local addresses on the router. To send gateway traffic over Tailscale later, widen the PC's 1883 rule to `100.64.0.0/10`.

## 2026-11-11 (Wednesday)

**What instructions improve output in new sessions, with Opus 5.5 as orchestrator and Haiku 5.5 doing deterministic tasks?**
Checked Claude Code's docs on subagents and CLAUDE.md. Added `.claude/agents/haiku-runner.md` and `haiku-scout.md` (model `claude-haiku-5-5`, restricted tools, no nested agents), `.claude/settings.json` (main model `claude-opus-5-5`, subagent nesting off), and to `CLAUDE.md`: "How to work: lead and workers", "Working style" and "Known pitfalls". Decision recorded in `decisions.md`.

**Keep Contec_ipc_to_cloud as the main repository and replicate the Claude agents and use cases with GPT 6.1 Sol and GPT 6 Luna.**
Fast-forwarded the Windows checkout to `c12ca02`. The source is `.claude/agents/`, containing runner and scout definitions, with the lead workflow in `CLAUDE.md`. Added `AGENTS.md`, `.codex/config.toml` and two standalone Codex roles: Sol leads; Luna at low reasoning handles exact commands/edits and sourced read-only lookups. Preserved lead-owned decisions, report formats, short-task rule, three-worker cap, one-level spawn depth and session-end log/commit/push workflow. Documented the mapping and Codex permission differences in `docs/codex-agents.md`; linked it from README and updated working setup. Both roles loaded in a fresh CLI session; scout evidence and runner exact-edit smoke tests passed and were independently checked. TOML parsing, effective configuration and unchanged safety rules were checked. The initial read-only sandbox prevented Python startup and the runner correctly reported blocked. No gateway application code or physical equipment changed.

**Finish the project setup on this PC using Luna Scout and Luna Runner, without router IP reservations.**
Started the four-service home-lab stack locally with generated ignored credentials. Bound MQTT to the connected Wi-Fi address `192.168.1.20`, Grafana to loopback, and this project's database to loopback port 5433 to preserve the existing PostgreSQL on 5432. Applied a Private, adapter/address/subnet-scoped MQTT firewall rule and enabled Docker Desktop start at sign-in. A temporary LOCAL simulator and read-only gateway produced 10 samples/70 metric rows; Grafana's authenticated datasource query passed. All containers restarted and the 70 rows persisted. Luna Runner's 18 gateway tests were independently rerun successfully. Current DHCP addresses are accepted; router reservations are optional. Updated Compose settings, example environment, network helper, both guide sources/output, decisions and logs. The laptop/IPC setup and an incoming connection from another physical device remain untested; no remote device was changed. Full PC reboot recovery remains untested. → [topics/08](topics/08-home-pc-setup.md)

**Apply all orchestrator/worker upgrades to both Sol/Luna and Opus 5.5/Haiku 5.5.**
Added a shared workflow, linked from both lead instructions and all four worker files: evidence/metadata checks, capability preflight and blocked handback, bounded artifacts, Windows UTF-8/exact-edit helpers, executable lead acceptance, read-only project health checks and an observed delegation scorecard. Preserved models, effort, tool restrictions and control safety. Final tools suite: 18 passed; gateway suite: 18 passed; live infrastructure health passed and offline telemetry was correctly rejected. Both Luna roles and both Haiku roles were exercised; Claude runtime metadata reported the selected Opus/Haiku 5.5 IDs. Recorded a lead launcher bug, a failed CLI invocation and a rejected Haiku Scout metadata claim rather than treating every handoff as successful; corrected the launcher/instructions and rechecked. Updated both setup docs, README, decisions and logs. Fresh Codex chat required to load revised role definitions. → [topics/09](topics/09-agent-workflow-upgrades.md)

**Finish all three home-lab devices from the IPC gateway dependency installation step (access checkpoint).**
Confirmed cloud health and both Tailscale peers. The laptop simulator returned all seven Modbus tags; a temporary read-only home-PC gateway collected 12 samples/84 database rows from it, and authenticated Grafana datasource queries passed. The IPC's RDP port was reachable, but neither remote device offered a command shell. The owner chose one-time access scripts: prepared scoped Windows PowerShell remoting, local credential prompts/DPAPI storage, cleanup instructions, and mocked fail-closed tests. Windows PowerShell 5.1 syntax checks and existing 18 gateway/18 helper tests passed. No remote device changed yet; the actual IPC path, service installation and reboot/recovery acceptance await the owner's bootstrap. The goal remains active. → [topics/10](topics/10-three-device-commissioning.md)

**Continue commissioning while one-time command access is pending.**
Rechecked both devices: PowerShell remoting remained unavailable and local credential files were absent. Sent the bootstrap script directly to both devices with Tailscale file transfer; both commands reported successful sends. Updated the access handoff instructions. The owner still needs to receive/run the script and enter credentials locally; file transfer is not evidence of remote setup completion. → [topics/10](topics/10-three-device-commissioning.md)

**Access dependency audit after three consecutive goal turns.**
At `2026-11-11T02:27:30Z`, neither device accepted WinRM connections and neither credential file was present. With scripts prepared and delivered, further remote commissioning requires owner execution and local credential entry. Recorded the goal as blocked pending that external change; IPC configuration, service installation and actual three-device/recovery acceptance remain incomplete. → [topics/10](topics/10-three-device-commissioning.md)

**Which credentials belong in the desktop prompts, and how does cleanup work after pasting the scripts?**
Explained first IPC Windows administrator credentials, then laptop Windows administrator credentials (`whoami` on that device identifies the account); passwords rather than PINs. The owner then reported both remote devices READY. Independent probes at `2026-11-11T04:04:34Z` confirmed TCP 5985 open on both; desktop credential files were still absent. Clarified that `-Disable` belongs to the saved-script invocation, and that cleanup can still be performed after a pasted setup, once the saved policy state is verified. No cleanup or authenticated remote configuration was performed. → [topics/10](topics/10-three-device-commissioning.md)

**Continue through the IPC login while resolving the laptop PIN-only login.**
Authenticated to the IPC, verified UWF OFF, unattended Tailscale, matching source/dependencies and both network paths; created its read-only config and installed the automatic NSSM gateway service. Process-crash recovery passed in 5.95 s, actual three-device telemetry reached DB/Grafana, and a Start request was rejected because control is disabled. A broker outage exposed a real replay race: gateway reconnect preceded ingest subscription and 30 samples were lost. Set ingest to a persistent MQTT session, rebuilt only ingest, and verified zero missing sequences through repeated 20-second and full-minute outages. Grafana returned all seven current IPC metrics. Supplied a separate temporary laptop administrator account/password method and clarified single-command secure password entry. Laptop authentication/startup, isolated bench commands, full-device reboots and cleanup remain pending; IPC has a pending servicing reboot and only about 5.1 GiB free, so no OS servicing/reboot was attempted before backup/space review. → [topics/10](topics/10-three-device-commissioning.md)

**Finish the laptop service and simulator-only command acceptance.**
The temporary laptop administrator login succeeded. Verified its simulator source/dependencies and actual LAN route, installed automatic NSSM `ipc-simulator`, replaced the manual instance, restricted its listener to `192.168.1.10:5020`, added the project LAN firewall rule and changed the IPC to that LAN host. Simulator process recovery passed in 7.11 s. A separate temporary in-memory IPC gateway proved Start/Stop by telemetry, duplicate-once execution, expiry/allowlist/TTL/offset refusals, LOCAL-mode refusal and heartbeat-loss fault 9, then exited cleanly. Restored simulator REMOTE/stopped/fault 0 and verified durable gateway control/heartbeat remained disabled. The owner reports laptop Run unattended enabled; private Tailscale preference access remains denied to the temporary account, so no bypass was attempted. Both permanent services run; CFast/servicing and physical/full-reboot acceptance plus cleanup still remain. → [topics/10](topics/10-three-device-commissioning.md)

**Confirm the CFast backup and preserve owner helper commits before reboot acceptance.**
The owner reports a verified CFast backup exists; the image was not independently inspected. Preparing a normal IPC servicing reboot. Fetched two additive owner commits for `sentence1`/`sentence2`; preserved the eight owned working files in ignored backups/stash, fast-forwarded the clean branch, restored byte-for-byte and dropped only the task's verified stash. Both owner helper files remain untouched. → [topics/10](topics/10-three-device-commissioning.md)

**Default Grafana to the live machine and begin approved reboot acceptance.**
Provisioned `press-01` as the dashboard default and verified reload through the authenticated API. Corrected a local launcher JSON serialization issue before any restart was sent; Windows then refused a normal remote restart because another user was logged on. The owner approved forced IPC then laptop restarts after saving work. Following a pause/resume, verified no previous reboot or live launcher, then issued the single approved forced IPC request at `2026-11-11T05:12:00Z`. Event 1074 confirms initiation; the same live monitor remains waiting while TrustedInstaller/TiWorker process pending servicing. Gateway remains online during shutdown preparation. Reboot recovery is not yet claimed. → [topics/10](topics/10-three-device-commissioning.md)

**Verify unattended reboot recovery and prepare the remaining IPC updates.**
The IPC rebooted at `05:35:19Z`, completed pending servicing to registry build `14393.2906` and restarted its gateway/Tailscale/WinRM before sign-in. Replaced the obsolete monitor shell with a fresh observation session; no duplicate restart. The approved laptop reboot at `05:48:18Z` recovered simulator/Tailscale/WinRM and the same LAN listener before sign-in. Three-device freshness passed. Verified Microsoft's LTSB update prerequisites and downloaded/hash-checked x64 SSU/baseline/security packages. The SSU task reported already installed, independently confirmed by QFE. DISM recommended component cleanup, so started supported cleanup without ResetBase as a monitored one-time SYSTEM task; it is still running. Large cumulative installs, desktop reboot, physical acceptance, final image and cleanup remain pending. → [topics/10](topics/10-three-device-commissioning.md)

**Remove the final CFast image from scope at the owner's request.**
The owner explicitly declined the final backup, so it is no longer an acceptance requirement and no new image will be created. Other setup work continues. Component cleanup remains CPU-active; started only the verified-source baseline download into protected IPC staging, with size/hash checks before use. No cumulative installer has been started. → [topics/10](topics/10-three-device-commissioning.md)

**Verify the IPC's baseline download and prepare desktop reboot acceptance.**
The baseline download completed at `06:44:31Z`; lead re-hashing on the IPC matched its exact size and SHA-256. Cleanup remains active and has marked a restart pending; no parallel cumulative install or restart was sent. Desktop AutoStart/service/freshness preflight passed, and the owner was asked for desktop restart approval because it will close Codex/other apps. → [topics/10](topics/10-three-device-commissioning.md)

**Close actual housekeeping gaps while servicing continues.**
Guide audit found SMBv1 enabled and time sync stopped. Disabled server SMBv1, made all firewall inbound defaults explicitly Block, and enabled/started automatic Windows Time; NTP resync and continued telemetry passed. Full SMBv1 feature/client removal and final clock accuracy remain queued. Verified the existing Contec utility/drivers and its installed BX-220D/LTSB 2016 documentation; no utility reinstall or watchdog change. Independently accepted Luna Scout's bounded vendor-document facts, with missing timing/tokens and invocation uncertainty retained. The same native cleanup remains active and progressing. → [topics/10](topics/10-three-device-commissioning.md)
