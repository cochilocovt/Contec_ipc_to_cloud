# Decisions

Newest at the bottom. When a decision changes, add a new entry rather than editing the old one.

### 2026-10-31 · Use the BX-220 as an edge gateway

The box reads the PLC and publishes to the cloud over MQTT; dashboards live in the cloud. It can keep driving its local screen at the same time. The two LAN ports separate the PLC network from the internet.

### 2026-10-31 · The PLC decides; the cloud only requests

For write access (start/stop): interlocks stay in the PLC, gated by a Local/Remote selector; E-stop is hardwired; the gateway runs only an allowlist of named commands; every command has an id and a short expiry; the UI confirms by telemetry; a heartbeat lets the PLC act on link loss. See architecture.md.

### 2026-10-31 · One data contract, whatever the hardware

Topics and payloads in data-contract.md are the same for the BX-220, a Pi or anything else. Only the tag map is hardware- and machine-specific.

### 2026-10-31 · Raspberry Pi 5 (2 GB) if a Pi POC is needed

Cheapest Pi that comfortably runs the gateway and tooling, and its code carries to CM5-based industrial gateways. Not yet bought.

### 2026-10-31 · Keep Windows 10 IoT Enterprise 2016 LTSB on the BX-220

Owner's choice over reinstalling Linux. Consequences: no security patches since 2026-10-13 unless ESUs are bought through Contec; the Unified Write Filter must be managed; Contec's RAS utility is available. Revisit before remote control goes live.

### 2026-11-03 · Python gateway scaffold

pymodbus 3.11 for Modbus TCP, paho-mqtt 2.1 for MQTT, YAML config, run as a Windows service with NSSM. Chosen for a fast start; Node-RED remains an option. Remote control is coded but `control.enabled` defaults to false.

### 2026-11-04 · Home lab: simulator first, KV-8000 later

Develop against the simulated PLC on a spare laptop. The final machine uses a different PLC, so the KV-8000 gets one limited session: set its IP, read DM registers from the IPC, and add a protocol option to the gateway. Its value is a second protocol (Keyence Host Link), real network behaviour, and rehearsing the Local/Remote and heartbeat ladder logic.

### 2026-11-04 · Home-lab cloud stack in Docker Compose

Mosquitto 2.0, TimescaleDB 2.17 on PostgreSQL 16, a Python ingest service, Grafana 11.3 with a provisioned dashboard and a read-only database login. Runs on this PC. Open broker for the LAN only; TLS, certificates and ACLs come before anything is exposed.

### 2026-11-04 · Remote admin through Tailscale and Remote Desktop

Tailscale on the IPC (key expiry disabled) with Remote Desktop over it, limited to the LAN and Tailscale addresses. No router port forwarding. Version 1607 has no built-in SSH server. Plant IT must approve Tailscale at the client site.

### 2026-11-05 · The client machine: pump test rig on a Keyence KV-X310

A small rig that measures the volumetric output of a soap-dispenser-style pump over many strokes and runs. The client wants live state, consistency analytics, and remote start/stop, servo adjustment and load cell adjustment. Designed in `docs/pump-test-rig/`, separate from the home lab, which stays as it is.

### 2026-11-05 · Proposed: OPC UA to the KV-X310, Host Link as fallback

The KV-X310's built-in Ethernet has a confirmed OPC UA server; Modbus TCP is confirmed only on the KV-XLE02 add-on unit. Needs a new gateway driver. Not built; confirm the server is enabled on the client's unit first.

### 2026-11-05 · Proposed: per-stroke records and bounded setpoint commands

The PLC measures each stroke and writes it to a results buffer that the gateway reads in full, instead of relying on 1 s polls. Setpoints become named commands carrying `params.value`, checked against limits in the backend, the gateway and the PLC, and applied only while the rig is idle. Still no generic register write. Not built; needs client sign-off.

## Open questions

- KV-X310 firmware, fitted units, OPC UA settings and the ladder program's variables (the client rig; see `pump-test-rig/client-questions.md`).
- Does the existing HMI keep running? Over RS-232 only one program can own the COM port.
- Production cloud: the home-lab stack on a VM with TLS, or AWS IoT Core / Azure IoT Hub.
- What sets `commands.status = confirmed`: the future backend, by comparing telemetry with the expected change.
- ESU pricing from Contec, or a date to move to LTSC 2021 / Linux.
- Servo and load cell details, and what "load cell adjustment" means. What the PLC does on heartbeat loss; whether remote Stop works in LOCAL.
