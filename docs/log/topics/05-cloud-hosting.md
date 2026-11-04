# Cloud hosting

## The home-lab stack (built 2026-11-04)

`cloud/docker-compose.yml` runs four services on the home PC:

| Service | Job, in plain words | Runs 24/7? |
|---|---|---|
| Mosquitto (MQTT broker) | Post office: takes readings from the gateway, delivers commands to it | Yes |
| Ingest service | Clerk: files every message into the database | Yes |
| TimescaleDB | Filing cabinet: telemetry, gateway status, commands, command events | Yes |
| Grafana | The window: "Machine overview" dashboard, read-only database login | Only while viewed |

Tested end to end in the workspace. The broker is open (no TLS, no passwords): LAN only. Setup steps in [../../home-lab.md](../../home-lab.md).

## Could Supabase and Vercel replace it? (2026-11-04)

| Job | Fit |
|---|---|
| Database | Supabase Postgres. TimescaleDB is deprecated on Supabase's Postgres 17 projects, so plain tables |
| Logins and roles for Start/Stop | Supabase Auth. The biggest win |
| Web app and buttons | Vercel for the page; Supabase Realtime for live status |
| "Check the user, record the command" | A Supabase or Vercel function |
| MQTT broker | Neither offers one |
| Always-on ingest | Vercel functions stop after minutes; doesn't fit |

**Proposed variant:** drop the broker. The gateway writes readings straight to Supabase over HTTPS as its own restricted user, and listens for new rows in `commands` through Supabase Realtime, checking for missed rows on reconnect. Everything runs over port 443, which plant firewalls usually allow. The safety rules, data format, PLC side and simulator stay the same; the gateway gains a Supabase connection module selectable in `gateway.yaml`.

Alternative: a free hosted MQTT broker plus an always-on ingest somewhere. More moving parts for no gain at this size.

## Free-plan catches (checked 2026-11-04)

1. Vercel Hobby is for personal, non-commercial use only. A client project needs Pro ($20 per developer per month) or a host that allows commercial use on its free plan.
2. Supabase free: 500 MB database per project, paused after a week of inactivity, no daily backups.
3. The current schema stores 7 rows a second (about 600,000 a day) and would fill 500 MB in about a week. Fix: one row per reading with all values together, a reading every 5 s or on change, raw data kept 30 days: on the order of 100 MB a month.

## Recommendation

Learning now: Supabase free plus Vercel Hobby is fine, and keep the Docker stack for offline home use. Client: the same design on paid plans, agreed with the client before go-live. Not yet decided or built.
