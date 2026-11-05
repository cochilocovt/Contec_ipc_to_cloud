# Keyence KV-X310

Facts below are from Keyence's product pages, checked 2026-11-05. Anything marked "to confirm" needs the KV-X310 user manual or the client's KV STUDIO project.

## The PLC

The KV-X is Keyence's newest PLC family (announced around September 2024), above the KV-8000. The KV-X310 is the smaller CPU in the range; the KV-X500/X520 are the larger ones.

| Item | KV-X310 |
|---|---|
| Built-in I/O | 16 inputs, 16 outputs |
| Expansion | Up to 16 KV-8000/7000-series units, or 48 including KV-5000/3000 units with a KV-EB1 |
| Program | 8 MB; ladder, structured text, mnemonic; programmed in KV STUDIO |
| Variables | Up to 100,000 named variables, 384 KB retained |
| Built-in Ethernet | Yes, with an **OPC UA server** (details below) |
| OPC UA server | Up to 8 client sessions, 20 subscriptions per session, 2,000 monitored items, sampling 10 ms to 10 s, up to 10,000 published variables, security None / Sign / SignAndEncrypt, certificate or user-password login |
| Power | 24 V DC ±10% |
| Operating temperature | 0 to 55 °C (0 to 50 °C with KV-5000/3000 units) |

## How the gateway can talk to it

The gateway in `gateway/` only implements Modbus TCP. Options for this PLC:

| Route | Where | Status | Notes |
|---|---|---|---|
| **OPC UA** | Built-in Ethernet | Confirmed on the KV-X310 page | Reads variables by name, not register number. Has security and subscriptions. Python client: `asyncua` |
| **Host Link** (Keyence "upper link") | Built-in Ethernet, TCP 8501 on Keyence PLCs | To confirm for the KV-X310 built-in port | Simple text commands such as `RDS DM100.U 5`. Same protocol as the home KV-8000, so it can be rehearsed at home |
| MC protocol / SLMP | KV-XLE02 Ethernet unit; built-in port to confirm | Listed for the KV-XLE02 | Mitsubishi-style binary protocol; good libraries exist but adds nothing over the above |
| Modbus TCP | KV-XLE02 Ethernet unit | Listed for the KV-XLE02, not for the built-in port | Would let the current gateway work almost unchanged, but needs an add-on unit the client may not have |

**Proposal: OPC UA first, Host Link as the fallback.** OPC UA is confirmed on the built-in port, needs no extra hardware, and lets the tag map use the ladder program's variable names. It also has built-in encryption between gateway and PLC, though the PLC link stays on the isolated machine-side port either way. If the OPC UA server turns out to be unlicensed or disabled on the client's unit, Host Link is the simplest second choice.

Either way the gateway needs a new driver behind the same tag map idea. The tag map would carry node ids or device names instead of Modbus addresses, for example:

```yaml
plc:
  protocol: opcua                      # proposed, not implemented
  endpoint: opc.tcp://192.168.10.10:4840
read:
  rig_state:     { node: "ns=4;s=Rig.State", enum: { 0: IDLE, 1: RUNNING, 2: STOPPING, 3: FAULT } }
  weight_g:      { node: "ns=4;s=LoadCell.Weight_g" }
  stroke_count:  { node: "ns=4;s=Run.StrokeCount" }
```

The node ids above are placeholders; the real ones come from the client's KV STUDIO project. Port 4840 is the OPC UA default; confirm what the KV-X310 uses.

## Servo hardware

Keyence's KV-X motion units, for reference:

| Unit | Network | Axes |
|---|---|---|
| KV-XH16EC | EtherCAT | 16 |
| KV-XH04ML / KV-XH16ML | MECHATROLINK-III | 4 / 16 |

The rig's servo might use one of these, a third-party drive on a network, or pulse outputs. For the cloud it makes no difference: the PLC owns all motion. The cloud only sends bounded setpoints, and the PLC applies them through its own motion logic. What matters is which setpoints the client wants to change ([control.md](control.md)).

## Load cell hardware

A load cell gives a millivolt signal, so something sits between it and the PLC:

- **Weighing indicator or transmitter** (third party) with a digital link (Ethernet, RS-232/485) or an analog output into a PLC analog input unit.
- **Keyence KL-LC1** is a Keyence load cell unit, but its page lists only older KL-link masters (KV-1000/700 and earlier), not the KV-X. Don't assume it fits.

Resolution matters a lot for this machine. See "Can the load cell resolve one stroke?" in [data-and-analytics.md](data-and-analytics.md).

## What the PLC program must provide

This is the contract between the ladder program and the gateway. Names are proposals; whoever writes the ladder chooses the real ones, and the tag map follows.

**State, read every poll:**

| Variable | Type | Meaning |
|---|---|---|
| `Mode` | enum | LOCAL / REMOTE, from the panel selector |
| `RigState` | enum | IDLE, RUNNING, STOPPING, FAULT (more if the ladder has them) |
| `FaultCode` | int | 0 = none |
| `RunNo` | uint32 | Increments at each run start, local or remote |
| `StrokeCount` | uint32 | Strokes done in the current run |
| `StrokesTarget` | uint32 | Strokes planned for the run |
| `LastRunEnd` | enum | Why the last run ended: completed, stopped, fault |
| `Weight_g` | real | Live, filtered load cell reading |
| `CupWeight_g` | real | Total in the collection cup, for the "cup full" check |
| `Servo.ActualPos_mm` | real | Live servo position |
| `Servo.Ready`, `Servo.Homed` | bool | Servo status |
| Active setpoints | real | Every value the cloud can change, echoed back so the UI can confirm it took effect |

**Per-stroke results buffer.** The PLC measures each stroke itself (weight before, weight after, settled) and writes a record into a ring buffer. A 1 s poll of live values would miss strokes or count one twice.

| Field | Type |
|---|---|
| `Results[i].RunNo` | uint32 |
| `Results[i].StrokeNo` | uint32 |
| `Results[i].Mass_g` | real |
| `Results[i].StrokeTime_ms` | uint32 |
| `Results[i].StrokeSetpoint_mm` | real (the setting in force for that stroke) |
| `Results[i].Flags` | bitmask (unsettled reading, overrange, servo fault during stroke…) |
| `ResultsWriteIndex` | uint32, total records ever written |

The gateway remembers the last index it read (saved to disk, so a restart neither loses nor repeats records), reads everything newer, and publishes each record. If the PLC has written more than the buffer holds since the last read, the gateway reports the gap. The database also ignores a repeated `(run_no, stroke_no)`.

**Command handling:**

- Pulse bits for Start, Stop, Tare, each acted on by the PLC only when its own conditions hold.
- Setpoints written to a **staging** variable, then an Apply bit. The PLC checks the staged value against its own limits and either copies it to the active setpoint or sets a rejection code. The active value comes back in telemetry.
- Heartbeat watch: if the gateway's heartbeat stops changing for a set time while a remotely started run is going, the PLC stops the run and sets a fault code.
- Interlocks that stay in the ladder whatever the cloud sends: cup full, servo not ready or not homed, load cell overrange, door or guard if the rig has one, and the hardwired E-stop.

## To confirm

- Whether the client's KV-X310 has the OPC UA server enabled, and its port and security settings.
- Whether the built-in port accepts Host Link (8501) and MC protocol.
- Which expansion units are fitted: Ethernet, motion, analog, anything for the load cell.
- Whether the ladder program exists yet, and who maintains it.

Sources: Keyence [KV-X310 page](https://www.keyence.co.in/products/controls/plc-building-block-type/kv-x/models/kv-x310/), [KV-XLE02 page](https://www.keyence.com/products/controls/plc-building-block-type/kv-x/models/kv-xle02/), [KV-XH16EC page](https://www.keyence.co.in/products/controls/plc-building-block-type/kv-x/models/kv-xh16ec), [KL-LC1 page](https://www.keyence.co.in/products/controls/plc-building-block-type/kv-8000/models/kl-lc1), and the KV-X announcement on [control.com](https://control.com/news/kv-x-the-latest-generation-in-plc-technology-from-keyence/). Ethernet options per CPU from an OPC server vendor's list ([faweb.net](https://www.faweb.net/product/opc/plc/kkv/unit)).
