# ipc_connection

Real-time cloud monitoring, and later remote start/stop, for a manufacturing machine. A Contec BX-220 box PC on site acts as the edge gateway. It reads the machine's PLC over Modbus, publishes to an MQTT broker in the cloud, and runs a short allowlist of commands that come back down.

```
Client web app ── Backend API ── MQTT broker      (cloud)
                                     │  outbound TLS only
              Edge gateway (BX-220) ─┘             (plant)
                     │ Modbus
                    PLC  ── motor, sensors, hardwired E-stop
```

## Status

| Area | State |
|---|---|
| Hardware | BX-220D-DC781724 in hand, staying on its Windows 10 IoT Enterprise 2016 LTSB install |
| Gateway code | Scaffold works against the simulated PLC: polling, telemetry, offline buffer, commands, heartbeat |
| Real PLC | Not connected yet. Final machine's PLC not known; a Keyence KV-8000 is available for testing |
| Cloud side | Home-lab stack in `cloud/` (MQTT, TimescaleDB, ingest, Grafana) tested end to end. No TLS or auth yet |
| Remote control | Coded but off by default. Needs the plant's sign-off first |

To run the whole chain across this PC, a spare laptop and the BX-220, follow [docs/home-lab.md](docs/home-lab.md). Bench setup progress is tracked in [docs/bx220-setup-checklist.html](docs/bx220-setup-checklist.html). Open it in a browser; ticks are saved in that browser.

## Layout

```
gateway/                 Python edge gateway
  ipc_gateway/           config, PLC access, command rules, main loop
  config/                gateway.example.yaml (copy to gateway.yaml, which git ignores)
  tests/                 unit tests for command rules and value decoding
cloud/                   home-lab cloud stack (docker compose)
  mosquitto/             broker config (open, LAN only)
  db/init/               TimescaleDB schema and read-only Grafana login
  ingest/                MQTT -> database service
  grafana/               datasource and "Machine overview" dashboard
tools/
  sim_plc.py             simulated PLC (Modbus TCP) with the same register map
  run-sim.bat            runs the simulator on a Windows laptop for the network
  send_command.py        sends one command over MQTT and prints the acks
docs/
  home-lab.md            three-machine setup: this PC, spare laptop, BX-220
  architecture.md        how read and write paths work, and the safety rules
  data-contract.md       MQTT topics, payloads, tag map format, database tables
  hardware.md            BX-220 notes, Windows support status, alternatives, Pi POC
  decisions.md           decision log and open questions
  bx220-setup-checklist.html
```

## Run it on one Windows machine

Quickest way to try the gateway alone. You need Python 3.10 or newer (64-bit) and an MQTT broker: either `docker compose up -d` in `cloud/` (see home-lab.md) or Mosquitto for Windows from mosquitto.org started with `mosquitto -v`.

```powershell
cd gateway
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt pytest
copy config\gateway.example.yaml config\gateway.yaml

# terminal 1: simulated PLC
python ..\tools\sim_plc.py --port 5020 --heartbeat-timeout 6

# terminal 2: gateway
python -m ipc_gateway --config config\gateway.yaml

# terminal 3: watch topics, then try a command
mosquitto_sub -t "factory/#" -v
python ..\tools\send_command.py motor_start
```

`send_command.py` is rejected with "control is disabled" until you set `control.enabled: true` in `gateway.yaml`. Run the tests with `python -m pytest` from `gateway/`.

## Run as a Windows service

Use [NSSM](https://nssm.cc) so the gateway starts at boot and restarts if it exits. NSSM sends Ctrl+C on stop, which the gateway handles as a clean shutdown.

```powershell
nssm install ipc-gateway C:\ipc_connection\gateway\.venv\Scripts\python.exe "-m ipc_gateway --config config\gateway.yaml --log-file logs\gateway.log"
nssm set ipc-gateway AppDirectory C:\ipc_connection\gateway
nssm set ipc-gateway Start SERVICE_AUTO_START
nssm set ipc-gateway AppExit Default Restart
nssm start ipc-gateway
```

If the Unified Write Filter is on, exclude `gateway\config` and `gateway\logs`, or changes and logs vanish at reboot.

## Safety rules

Read [docs/architecture.md](docs/architecture.md) before touching the write path. In short: the cloud only requests and the PLC decides; the hardwired E-stop never passes through software; only allowlisted commands with a short expiry are ever written.
