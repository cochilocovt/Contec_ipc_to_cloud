# Remote control

The client wants remote start/stop, servo adjustment and load cell adjustment. Everything here is a proposal; nothing is implemented. The write-path rules in [../architecture.md](../architecture.md) still apply in full: the PLC decides, the E-stop is hardwired, commands come from an allowlist, carry an id and expire, and the UI waits for telemetry to confirm.

## Proposed commands

| Command | Kind | Allowed when (PLC checks; gateway pre-checks) | Confirmed in telemetry by |
|---|---|---|---|
| `run_start` | pulse | REMOTE, IDLE, no fault, servo ready and homed, cup not full | `RigState` = RUNNING and `RunNo` +1 |
| `run_stop` | pulse | RUNNING (see the LOCAL-mode question below) | `RigState` leaves RUNNING |
| `set_stroke_mm` | setpoint | REMOTE, IDLE | `Servo.StrokeSetpoint_mm` equals the value |
| `set_stroke_speed` | setpoint | REMOTE, IDLE | active speed equals the value |
| `set_strokes_target` | setpoint | REMOTE, IDLE | `StrokesTarget` equals the value |
| `set_stroke_interval_ms` | setpoint | REMOTE, IDLE | active interval equals the value |
| `loadcell_tare` | pulse | REMOTE, IDLE, reading stable | `Weight_g` near 0 |

The setpoint names assume the servo presses the pump and the client wants to change its stroke. Replace them once the client says what "servo adjustment" means. Units and limits come from the client and the mechanical design.

Setpoints only change while the rig is IDLE, so every stroke in a run uses the same settings and the run's analytics compare like with like. Each stroke record also stores the setpoint in force, in case this rule is ever relaxed.

## Commands that carry a value (change to the data contract)

Today the cloud cannot pass a value: [../data-contract.md](../data-contract.md) maps each command to a fixed write. Setpoints need a number, so the contract needs one addition. The rule against a generic "write register" command stays: each setpoint is still a named command with its own limits.

Command payload, with `params.value` added:

```json
{
  "cmd_id": "8d1e0c52-2f4b-4c1a-9a63-5b0f2e7d3a90",
  "command": "set_stroke_mm",
  "params": { "value": 12.5 },
  "issued_by": "operator@client.com",
  "issued_at": "2026-11-20T06:30:00Z",
  "expires_at": "2026-11-20T06:30:10Z"
}
```

Gateway config for a setpoint command (proposed):

```yaml
control:
  commands:
    set_stroke_mm:
      type: setpoint
      stage: "ns=4;s=Servo.StrokeStage_mm"   # where the value is written
      apply: "ns=4;s=Servo.StrokeApply"        # bit pulsed after the write
      min: 2.0
      max: 20.0
      step: 0.1
      requires_state: IDLE
```

Checks, in order:

1. **Backend** (web app): the user's role, the value against the same limits, and a confirmation dialog showing old and new values.
2. **Gateway**: `params.value` present, a number, within `min`/`max`, a multiple of `step`, rig in REMOTE and IDLE, plus the usual id, expiry and duplicate checks. A value outside the limits is rejected, never clamped.
3. **PLC**: checks its own limits again, then copies staging to active or sets a rejection code. The PLC's limits are the real ones; the gateway's are a courtesy that gives a clear message.

`executed` still only means the write succeeded. The UI shows the new value as confirmed only when telemetry echoes it as the active setpoint.

## What stays local

Not offered remotely, at least at first:

- **Jogging the servo, or any manual motion.** Network delay makes "move while held" unsafe.
- **Homing**, unless the client asks and the PLC makes it safe to do unattended.
- **Fault reset.** Someone should look at the rig before it restarts after a fault.
- **Load cell calibration with reference weights.** Someone has to place the weights. A remote button could at most step through the procedure while a person is at the rig.
- **Anything during a run except Stop.**

## "Load cell adjustment": what it might mean

To ask the client. Each reading leads to a different design:

| Meaning | Remote? | Notes |
|---|---|---|
| Tare / zero before a run | Yes | Simple pulse, `loadcell_tare` above |
| Span calibration with a known weight | Only as a guided step with someone at the rig | Store each calibration (date, weight, result) for traceability |
| Filter or settling settings (filter strength, settle time, stability band) | Yes, as bounded setpoints | Changes measurement results, so record the settings with each run |
| Physical position of the load cell or cup (a second axis) | Yes, as a bounded setpoint, like the servo | Needs its own interlocks |

## Open points on control

- **Stop in LOCAL mode.** The gateway's `require` check currently applies to every command, so a remote Stop is refused in LOCAL. Some plants want Stop to work from anywhere. The client decides; if Stop should always work, the gateway needs a per-command mode rule.
- **Heartbeat loss during a remote run.** Proposed: the PLC stops the run and sets a fault. A run started locally might carry on. The client decides.
- **Who may change setpoints.** Probably a separate role from who may start runs.
- **The OS.** The BX-220 is on Windows 10 IoT 2016 LTSB, out of support since 2026-10-13. Settle ESUs or a move before remote control goes live, as already noted in [../decisions.md](../decisions.md).

## Before remote control goes live

- Client signs off the command list, limits and LOCAL/REMOTE behaviour.
- Ladder program enforces every interlock and limit on its own (test by sending bad values straight to the PLC, bypassing the gateway).
- Heartbeat loss tested: unplug the gateway mid-run.
- Broker TLS, per-device certificates and ACLs in place; only the backend can publish commands.
- Audit log reviewed: every command, who sent it, every ack, and the confirmation.
