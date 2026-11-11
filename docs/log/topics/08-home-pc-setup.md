# Home PC setup

## 2026-11-11: installed and tested on this PC

The owner asked to finish this PC using Luna Scout and Luna Runner, and to proceed without router DHCP reservations. Use the current addresses and keep automatic DHCP. Do not choose manual addresses from an unknown router DHCP pool.

| Item | Verified setup |
|---|---|
| Connected adapter | Wi-Fi, home network set to Private |
| PC broker | `192.168.1.20:1883`, bound only to that LAN address |
| IPC reachability | `tailscale ping --c 1 ipc` responded directly through `192.168.1.3`; Tailscale address `100.89.184.100` |
| Laptop | Tailscale peer `mom-laptop` was offline; spare-laptop LAN address not confirmed |
| Grafana | `http://localhost:3000`, loopback only, login `admin` |
| Project database | `127.0.0.1:5433`; the pre-existing PostgreSQL 18 service remains running on 5432 |
| Local configuration | Three randomly generated passwords in ignored `cloud/.env`; Grafana uses `GRAFANA_ADMIN_PASSWORD`. No credentials in git or this log |
| Firewall | `IPC-HomeLab-MQTT`: Private, inbound TCP 1883, Wi-Fi only, local address `192.168.1.20`, remote `LocalSubnet` |
| Startup | Docker Desktop start-at-sign-in enabled and saved; all containers use `unless-stopped` |
| Python | Ignored `gateway/.venv`, Python 3.11.9, pinned gateway requirements plus pytest 9.2.0 |

### Verified

- Luna Runner installed the isolated Python environment and ran the gateway tests: 18 passed. The lead independently reran them: 18 passed.
- Compose configuration validated without printing credentials. Four services are running; TimescaleDB is healthy. Actual host listeners match the LAN/loopback addresses above.
- The network helper ran elevated successfully; the lead checked the resulting profile, address filter and TCP port filter.
- A temporary simulator listened only on `127.0.0.1:15020` in LOCAL mode. A temporary gateway identified as `home-lab/setup-check` read 10 samples with control and heartbeat writes disabled. The motor stayed stopped.
- MQTT ingest stored 70 rows covering all 7 metrics. Authenticated Grafana checks passed for its health, TimescaleDB datasource health, provisioned Machine overview dashboard, and a real datasource query returning 7 metrics.
- The temporary simulator and gateway stopped; `setup-check` is offline. Its labelled historical data remains intentionally available.
- All four containers restarted, ingest reconnected to MQTT and the database, Grafana health passed, and all 70 test rows persisted.
- Docker's saved `AutoStart` setting is true. A full PC reboot/sign-in recovery has not been tested.
- The bundled guide JavaScript passed Node's syntax check after its exact text updates.
- Grafana's database login can SELECT telemetry and cannot INSERT or DELETE it.
- The current Windows power plan already has AC sleep set to Never; it was not changed.

### Remaining

This PC's cloud services are ready. The three-device test still needs the spare laptop simulator and the gateway on the IPC. No software was installed on either remote device this session, and incoming MQTT from another physical device was not tested. Follow the existing IPC UWF/backup/update checks before installing the gateway. Remote machine control remains disabled.

If the PC address changes, update `MQTT_BIND_ADDRESS` in `cloud/.env`, run `docker compose up -d` from `cloud/`, reapply `tools/enable-home-lab-network.ps1` elevated with the new address, and update the IPC gateway MQTT host. If the laptop address changes, update the gateway PLC host. Keep Grafana/database on loopback and do not forward the open broker through the router.

Use `docker compose ps` to inspect and `docker compose up -d` to start the stack from `cloud/`. Keep the existing `.env`; do not copy the example over it. Stop with `docker compose stop` to preserve data. Never use `down -v` without specific authorization.

Docker networking reference checked 2026-11-11: [Networking in Compose](https://docs.docker.com/compose/how-tos/networking/) explains service-name discovery and the separation of host and container ports.
