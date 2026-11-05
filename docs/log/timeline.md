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
