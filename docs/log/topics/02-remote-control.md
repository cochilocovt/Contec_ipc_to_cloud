# Remote control (start/stop)

## Safety rules (2026-10-31)

Once a remote click can move equipment:

- **The PLC decides; the cloud only requests.** Interlocks stay in the PLC, which accepts remote commands only when the panel's Local/Remote selector is on Remote.
- **The E-stop is hardwired** and never passes through software or the cloud. A dashboard "Stop" is a normal stop, never labelled E-Stop.
- **Allowlist, not raw writes.** The gateway runs only named commands (`motor_start`, `motor_stop`), each mapped to one coil or register. The cloud can never say "write register 40011 = 1".
- **Every command has an id and an expiry.** A start that arrives late after a network hiccup is rejected. Duplicates run once.
- **Confirm by feedback.** "Executed" only means the write succeeded; the UI waits for telemetry to show the change.
- **Link loss is defined.** The gateway bumps a heartbeat register; the PLC decides what to do when it stops (the simulator stops the motor and sets fault 9).
- **Security:** per-device certificates, broker ACLs, operator roles with 2FA, an audit trail, no inbound ports on the gateway. Moving off the unpatched OS (or buying ESUs) becomes a requirement.

All of this is implemented in `gateway/` and documented in [../../architecture.md](../../architecture.md). Control is off by default (`control.enabled: false`).

## How a client uses a Start/Stop button (2026-11-04)

Through a small web app with its own backend. Grafana stays read-only. The browser never talks to MQTT or the machine: if it did, it would hold broker credentials that can command any machine.

```
Browser ──HTTPS──> Backend API ──MQTT──> Broker ──> Gateway ──Modbus──> PLC
```

When someone presses Start:
1. **Login** with two-factor authentication; roles per machine (viewer, operator, admin). Only operators see Start/Stop.
2. **The button knows the state.** It is enabled only if the gateway is online, the last reading is under about 5 s old, the machine is in REMOTE, and there's no fault. Otherwise it's greyed out with the reason shown.
3. **Confirmation** dialog for Start ("confirm the area is clear"). Stop should be easy; Start careful.
4. **The backend** checks the role again, fills `issued_by` from the login session, creates `cmd_id` and a 10 s expiry, records the command, and publishes it.
5. **Live status** in the browser over WebSockets or server-sent events: Sending → Accepted → Executed → **Confirmed** when telemetry shows the change. If not confirmed within a few seconds, say so plainly.
6. **Audit** from the `commands` and `command_events` tables.

Plants may add an on-site "remote enabled" key switch, or allow only Stop remotely. That is configured in the PLC and already supported through the REMOTE mode check.

### Ways to build it

| Option | Notes |
|---|---|
| Own app: FastAPI backend + React | Most work, full control, fits the existing stack |
| IoT platform such as ThingsBoard | Users, roles and command widgets built in; work inside its model |
| Button plugin on Grafana | Demo only: weak per-user permissions and confirmation |

What exists: everything from the broker down. What's missing: the backend API with logins and roles, the web page, and broker rules so only the backend can publish commands. Hosting choice affects this; see [topic 05](05-cloud-hosting.md).

## Test results so far

Tested in the workspace with the simulator: start/stop accepted and executed; expired, unknown and LOCAL-mode commands rejected with reasons; gateway crash made the PLC stop the motor (fault 9) and the dashboard show Offline; a broker outage caused no data gap.
