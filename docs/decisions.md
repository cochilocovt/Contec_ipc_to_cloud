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

## Open questions

- PLC make, model and firmware; Modbus TCP or RTU over RS-232; the register map.
- Does the existing HMI keep running? Over RS-232 only one program can own the COM port.
- Cloud: self-hosted EMQX or Mosquitto on a VM, or AWS IoT Core / Azure IoT Hub.
- ESU pricing from Contec, or a date to move to LTSC 2021 / Linux.
- Which commands the plant actually wants, and what the PLC does on heartbeat loss.
