# Pump test rig (client machine)

The design lives in [../../pump-test-rig/](../../pump-test-rig/README.md). This note records how it came about and what was checked.

## The brief (2026-11-05)

The client machine is a small rig that measures the volumetric output of a liquid dispensing pump, like a hand-soap pump, to show how consistent a pump's output is across strokes and runs. The PLC is a Keyence KV-X310. The client wants remote start/stop, remote adjustment of a servo and of the load cell, and a dashboard with analytics. The owner asked for it to be documented separately, leaving the home-lab experiment as it is.

## What was checked (2026-11-05, Keyence product pages)

- KV-X310: 16 in / 16 out built in, 8 MB program, 24 V DC, built-in Ethernet with an OPC UA server (8 sessions, sampling 10 ms to 10 s, SignAndEncrypt available).
- Ethernet options listed for the KV-X310: built-in port, KV-XLE02, KV-XCM02. The KV-XLE02 lists Modbus/TCP, Host Link, MC protocol/SLMP and EtherNet/IP. Host Link and Modbus TCP on the built-in port are not confirmed.
- Motion units for KV-X: KV-XH16EC (EtherCAT, 16 axes), KV-XH04ML / KV-XH16ML (MECHATROLINK-III).
- Keyence's load cell unit KL-LC1 lists only older KL-link masters, not the KV-X, so a third-party amplifier or weighing indicator is likely.

## Points raised

- The gateway only speaks Modbus TCP: proposed OPC UA, with Host Link as fallback. The home KV-8000 is the same family and can rehearse Host Link and the ladder patterns.
- A 1 s poll can miss strokes, so the PLC should write per-stroke results to a buffer the gateway reads in full.
- Servo and run settings need commands that carry a value; today the cloud cannot send one. Proposed bounded setpoints, checked by backend, gateway and PLC, applied only while idle.
- "Load cell adjustment" is ambiguous (tare, calibration, filter settings, or position). Asked the client.
- Per-stroke weighing needs fine resolution: with a 1.0 mL ± 5% pump, roughly 0.01 g. A general-purpose load cell may not manage that, which could change the hardware.

## Node-RED as an option (2026-11-05)

Where it would sit: on the BX-220 instead of the Python gateway. Read flow (timer → PLC read → shape telemetry → MQTT out), stroke flow (read the results buffer from the last saved index → MQTT out), command flow (MQTT in → checks → PLC write → ack out). The cloud side does not change, because the topics and payloads stay the same.

| For | Against |
|---|---|
| Protocol nodes exist: OPC UA, Modbus, and a Keyence Host Link node (new, few users; its page names a KV-X500 test) | Allowlist, expiry, dedupe and setpoint limits move from `commands.py` and its tests into function nodes, harder to test and review |
| Quick to change while the client's answers come in; live debug view | Flows are one large JSON file; git diffs are hard to read |
| Plant engineers often know it and can maintain it | Offline buffer and the saved results index must be built (file-backed context helps) |
| | Node.js on Windows 10 1607 untested; Node-RED's Windows guide uses Task Scheduler, NSSM should also work |

Not a fit for: the client-facing control UI (logins, roles, audit stay in the web app) or anything safety-related (stays in the PLC).

Suggested: use Node-RED now as a bench tool to explore the KV-X310 (browse OPC UA variables, try Host Link) before writing the gateway driver. Keep the Python gateway for production unless the client's own staff will own the edge device, in which case Node-RED's maintainability may win.
