# Pump test rig (client machine)

**2026-11-13 machine-file assessment:** [ETO & Dose Tester review](machine-file-review-2026-11-13.md) adds evidence from the proposal, drawing, instrument orders and customer references. The design needs two channels: pressing force and dispensed dose. Ordered sensors are 100 N and 20 N, with a two-channel analog amplifier; installed mapping/ranges remain unverified. Read that assessment before using the earlier single-load-cell proposals below. The source folder does not independently confirm the PLC CPU or contain a PLC/HMI program.

Requirements captured 2026-11-05. Nothing in this folder is built yet: it is the design for the real client machine, kept apart from the home lab. The home-lab setup (`cloud/`, `gateway/`, `tools/`, `docs/home-lab*`) is unchanged and still runs against the simulated PLC.

## The machine

A small test rig that measures the volumetric output of a liquid dispensing pump, the kind used on hand-soap bottles. The rig actuates a pump over and over and measures what comes out of each stroke. The client wants to see how consistent a pump's output is within a run and across runs.

| Part | What we know | Still to confirm |
|---|---|---|
| PLC | Keyence **KV-X310** | Firmware, installed expansion units, the ladder program's variables |
| Servo | Present; the client wants to adjust it remotely | Make and model, how it connects to the PLC, what it adjusts (assumed: the stroke that presses the pump) |
| Load cell | Present; the client wants to adjust it remotely | Capacity, amplifier or weighing indicator, how it reaches the PLC, what "adjust" means |
| Edge gateway | The Contec BX-220, as in the home lab | Whether it also runs a local operator screen |

Assumed until the client says otherwise: output is measured by weight (gravimetric). The pump dispenses into a cup on the load cell, and volume = mass ÷ density of the test liquid.

## What the client wants

| Need | Where it is designed |
|---|---|
| See the rig's live state on a dashboard | [data-and-analytics.md](data-and-analytics.md) |
| Analytics on output consistency per stroke, per run and across runs | [data-and-analytics.md](data-and-analytics.md) |
| Remote start and stop of a test run | [control.md](control.md) |
| Remote adjustment of the servo | [control.md](control.md) |
| Remote adjustment of the load cell | [control.md](control.md), meaning still to confirm |

## How it fits the existing design

The chain is the same as in [../architecture.md](../architecture.md): PLC → BX-220 gateway → MQTT broker → ingest → database → dashboard, with commands coming back down through a backend API. The safety rules stay as they are: the PLC decides, the E-stop is hardwired, commands come from an allowlist and expire.

What this machine adds:

| Change | Why | Detail |
|---|---|---|
| A new PLC protocol in the gateway | The gateway only speaks Modbus TCP. The KV-X310's built-in port has a confirmed OPC UA server; Modbus TCP is confirmed only on the add-on Ethernet unit | [plc-kv-x310.md](plc-kv-x310.md) |
| Per-stroke records, not just 1 s samples | A 1 s poll of "latest value" can miss or double-count strokes. The PLC measures each stroke and the gateway reads every record | [data-and-analytics.md](data-and-analytics.md) |
| Commands that carry a value | Servo and run settings need numbers. Today the cloud cannot send a value at all | [control.md](control.md) |
| Test runs with metadata | Analytics need to know which pump sample, which liquid and which spec a run belongs to | [data-and-analytics.md](data-and-analytics.md) |
| A web app for control and run setup | Grafana stays for viewing; control and run setup need logins and roles (already decided in [../log/topics/02-remote-control.md](../log/topics/02-remote-control.md)) | [control.md](control.md) |

## Files

| File | What's in it |
|---|---|
| [plc-kv-x310.md](plc-kv-x310.md) | The PLC: what it is, how the gateway can talk to it, servo and load cell hardware, and what the ladder program must provide |
| [control.md](control.md) | The remote commands, setpoint limits, what stays local, and the change to the data contract |
| [data-and-analytics.md](data-and-analytics.md) | How output is measured, what the gateway sends, database tables, and the analytics and dashboard |
| [client-questions.md](client-questions.md) | Questions to send the client before any building starts |

## Work this implies (not started)

1. Get answers to [client-questions.md](client-questions.md), especially the servo, the load cell and the target output with its tolerance.
2. Agree the PLC-side variables and the results buffer with whoever writes the ladder program ([plc-kv-x310.md](plc-kv-x310.md)).
3. Gateway: an OPC UA (or Host Link) driver, a reader for the per-stroke results buffer, and bounded setpoint commands.
4. Cloud: `stroke` and `run` topics, `test_runs` and `strokes` tables, ingest for both.
5. Web app: login and roles, run setup form, Start/Stop, setpoint controls with limits, live run view.
6. Dashboard: the analytics panels in [data-and-analytics.md](data-and-analytics.md).
7. Pick the production cloud (still open in [../log/open-items.md](../log/open-items.md)).

## Relation to the home lab

The home lab stays as it is. One useful link: the KV-8000 at home is the same Keyence family and uses the same KV STUDIO software, so the planned KV-8000 session can rehearse the Host Link connection, the Local/Remote and heartbeat logic, and the results buffer handshake before touching the client's KV-X310.
