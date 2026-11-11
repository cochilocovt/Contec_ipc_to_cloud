# Home lab

Three machines on the same home network stand in for the plant and the cloud.

| Machine | Plays the part of | Runs |
|---|---|---|
| This PC | the cloud | Docker stack in `cloud/`: MQTT broker, TimescaleDB, ingest, Grafana |
| Spare laptop | the PLC | `tools/sim_plc.py` (simulated PLC) |
| BX-220 | the edge gateway | `gateway/` |

```
 Spare laptop                BX-220                     This PC
 sim_plc.py  :5020  <──Modbus── gateway ──MQTT──>  :1883 broker → ingest → TimescaleDB
                                                    :3000 Grafana  ← your browser
```

The KV-8000 can replace the laptop later. See decisions.md.

## 0. Write down the IP addresses

On each machine run `ipconfig` and note the IPv4 address. In the steps below:

- `PC_IP` is this PC
- `LAPTOP_IP` is the spare laptop
- `IPC_IP` is the BX-220

DHCP reservations are useful but are not a prerequisite for this lab. If the router does not allow them, use the current addresses and leave Windows on automatic DHCP. Do not pick a manual static address from an unknown DHCP pool: it could collide with another device. Recheck the addresses if a connection stops working.

On 2026-11-11 this PC's connected Wi-Fi address was `192.168.1.20`; the IPC responded directly at `192.168.1.3` (Tailscale `100.89.184.100`). The Tailscale peer `mom-laptop` was offline; the spare laptop's LAN address was not confirmed. See [the local setup record](log/topics/08-home-pc-setup.md).

## 1. This PC: start the cloud stack

Needs Docker Desktop.

```powershell
cd C:\Users\V.T\Documents\ipc_connection\cloud
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env                 # set three passwords and MQTT_BIND_ADDRESS=PC_IP
docker compose up -d --build
docker compose ps            # all four services should be Up; timescaledb (healthy)
```

On this PC the passwords have already been generated in the ignored `cloud/.env`; keep that file and do not overwrite it with the example. Grafana's login is `admin` with the value of `GRAFANA_ADMIN_PASSWORD` from that file. Never commit it.

Set `MQTT_BIND_ADDRESS` to this PC's home-LAN IPv4 address (`192.168.1.20` at setup). The default is loopback, so a fresh checkout does not expose the open broker. Do not set it to `0.0.0.0`. If this PC's address changes, update that value and the gateway's MQTT host, then run `docker compose up -d` again.

If port 5432 is already occupied by another PostgreSQL installation, set `DB_HOST_PORT=5433` (or another unused port) in `.env`. This PC uses `127.0.0.1:5433`; the existing PostgreSQL service stays on 5432. Containers still connect to `timescaledb:5432` internally.

Open http://localhost:3000. The "Machine overview" dashboard is empty until a gateway publishes. Grafana is bound to loopback and is accessible only from this PC.

Allow the gateway to reach the broker. In an admin PowerShell:

```powershell
# From cloud/; choose the connected adapter's name and current LAN address.
powershell -ExecutionPolicy Bypass -File ..\tools\enable-home-lab-network.ps1 -InterfaceAlias "Wi-Fi" -LanAddress 192.168.1.20
```

Run that helper only on the trusted home network. It sets the selected adapter's network profile to Private and allows inbound TCP 1883 only on that adapter, at the supplied address, from the local subnet. Neither Grafana nor this project's database is published to the LAN. No router port forwarding is needed.

All four containers use `restart: unless-stopped`. Docker Desktop must be running; its **Start Docker Desktop when you sign in** setting is enabled on this PC. After signing in, check `docker compose ps`. A container restart with data persistence has been tested; a full PC reboot has not. To stop without deleting data use `docker compose stop`; start again with `docker compose up -d`.

## 2. Spare laptop: run the simulated PLC

Install Python 3.10+ (tick "Add to PATH"), copy the `ipc_connection` folder over, then:

```powershell
cd ipc_connection
tools\run-sim.bat
```

Allow the gateway to reach it (admin PowerShell on the laptop):

```powershell
New-NetFirewallRule -DisplayName "Simulated PLC 5020" -Direction Inbound -Protocol TCP -LocalPort 5020 -Profile Private -Action Allow
```

Options: `tools\run-sim.bat --mode local` starts with the machine in LOCAL mode, where remote starts are refused.

## 3. BX-220: run the gateway

Once the IPC is backed up and updated (checklist phases 2–3), install Python 3.12 64-bit and copy the folder over.

```powershell
cd ipc_connection\gateway
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy config\gateway.example.yaml config\gateway.yaml
notepad config\gateway.yaml
```

In `gateway.yaml` change only:

```yaml
plc:
  host: LAPTOP_IP
  port: 5020
mqtt:
  host: PC_IP
  port: 1883
```

Test the path before starting:

```powershell
Test-NetConnection LAPTOP_IP -Port 5020     # TcpTestSucceeded : True
Test-NetConnection PC_IP -Port 1883         # TcpTestSucceeded : True
.venv\Scripts\python -m ipc_gateway --config config\gateway.yaml
```

Within a few seconds the dashboard shows Gateway Online and live readings. Set the IPC clock correctly first: readings are stored with the gateway's timestamp, so a wrong clock puts data in the wrong place on the charts.

## 4. Try the write path

Set `control.enabled: true` and `control.heartbeat.enabled: true` in `gateway.yaml` and restart the gateway. Then, from this PC (with Python and `gateway\requirements.txt` installed):

```powershell
python tools\send_command.py motor_start --host PC_IP --by vaibhav
python tools\send_command.py motor_stop  --host PC_IP --by vaibhav
```

The command and its result appear in "Recent commands" and the motor tile changes. Things to try:

| Do this | Expect |
|---|---|
| `--ttl -5` | `expired` |
| a made-up command name | `rejected`, "command not allowed" |
| restart the sim with `--mode local`, then start | `rejected`, "machine in LOCAL mode" |
| unplug the IPC's network cable for a minute while running | sim stops the motor within 6 s and sets fault 9; dashboard shows Offline after about 45 s (MQTT keepalive), then Fault 9 once reconnected |
| `docker compose stop mosquitto`, wait a minute, `docker compose start mosquitto` | no gap in the charts: the gateway replays what it buffered |

## Stopping and resetting

```powershell
docker compose stop          # keeps data
docker compose down -v       # deletes ALL data and recreates the database next time
```

`down -v` is also how you apply changes to `db/init/01-schema.sql`.

## This is not production

The broker accepts anyone on your network with no password, including on `cmd` topics. That is fine at home. Before the broker is reachable from outside your network: TLS on 8883, a client certificate per gateway, and topic ACLs (architecture.md, Security). The commands table records whatever `issued_by` the sender claims; a real backend sets it from the logged-in user.
