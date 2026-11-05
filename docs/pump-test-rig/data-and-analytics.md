# Data and analytics

What the rig measures, what the gateway sends, how it is stored, and what the dashboard shows. Proposals only; the home-lab schema and ingest in `cloud/` are unchanged.

## How output is measured

Assumed until the client confirms: by weight. The pump dispenses into a cup on the load cell. For each stroke the PLC takes a settled reading before and after, and the difference is the stroke's mass.

```
volume_ml = mass_g / density_g_per_ml
```

- **Store mass, compute volume.** The density belongs to the run (set in the run setup form). If it is corrected later, every volume recomputes.
- **Settle before reading.** Liquid keeps dripping after the stroke and the servo shakes the frame. The PLC waits for the reading to stay within a small band for a set time, and flags the stroke if it never settles.
- **The cup fills up.** The PLC tracks the cup's total weight and refuses to start, or stops, before the load cell's range is reached.
- **Temperature** changes liquid density and viscosity. Worth logging if the client cares about small differences.

### Can the load cell resolve one stroke?

This needs checking early, because it decides the hardware. A rule of thumb for measurement systems is that resolution should be about a tenth of the tolerance band or finer.

Example, not the client's numbers: a pump rated 1.0 mL ± 5% with a liquid near water's density gives a band of 0.10 g, so roughly 0.01 g resolution. A 500 g load cell read at 1 part in 20,000 resolves 0.025 g, which is too coarse to grade single strokes.

Ways out, depending on the client's numbers:

- A small-capacity load cell, or a precision balance with a digital output, and a light cup.
- Weigh every N strokes and divide. This works for the average but hides stroke-to-stroke variation, which is what the client wants to see.
- A draft shield and anti-vibration mounting.

Resolution is not repeatability. Before trusting results, weigh a known reference mass many times on the rig and check the spread.

## What the gateway sends

Topics follow [../data-contract.md](../data-contract.md). Two are new for this machine.

```
factory/{site}/{machine_id}/telemetry   as today, every poll
factory/{site}/{machine_id}/state       as today, retained
factory/{site}/{machine_id}/status      as today, online/offline
factory/{site}/{machine_id}/cmd         as today, plus params.value for setpoints
factory/{site}/{machine_id}/cmd/ack     as today
factory/{site}/{machine_id}/stroke      NEW: one message per stroke, QoS 1
factory/{site}/{machine_id}/run         NEW: run start and end, QoS 1
```

**Telemetry**, same envelope as today with this machine's metrics:

```json
{
  "ts": "2026-11-20T06:31:04.120Z",
  "machine_id": "pump-rig-01",
  "seq": 5021,
  "metrics": {
    "mode": "REMOTE",
    "rig_state": "RUNNING",
    "fault_code": 0,
    "run_no": 412,
    "stroke_count": 37,
    "strokes_target": 100,
    "weight_g": 38.214,
    "cup_weight_g": 38.214,
    "servo_pos_mm": 0.02,
    "stroke_setpoint_mm": 12.5
  }
}
```

**Stroke**, one per record read from the PLC's results buffer:

```json
{
  "ts": "2026-11-20T06:31:03.880Z",
  "machine_id": "pump-rig-01",
  "run_no": 412,
  "stroke_no": 37,
  "mass_g": 1.032,
  "stroke_time_ms": 640,
  "stroke_setpoint_mm": 12.5,
  "flags": 0,
  "buffer_index": 18233
}
```

Stroke messages go through the gateway's offline buffer like telemetry, but should not be dropped when it is full, since each one is a measurement. Proposed: a separate, larger queue saved to disk (excluded from the Unified Write Filter).

**Run**, published by the gateway when `RunNo` changes and when the rig leaves RUNNING:

```json
{"ts": "2026-11-20T06:30:20Z", "machine_id": "pump-rig-01", "run_no": 412, "event": "start",
 "settings": {"stroke_mm": 12.5, "stroke_speed": 50, "strokes_target": 100, "stroke_interval_ms": 1000}}
{"ts": "2026-11-20T06:32:05Z", "machine_id": "pump-rig-01", "run_no": 412, "event": "end",
 "reason": "completed", "strokes_done": 100}
```

`reason` is `completed`, `stopped` or `fault`, read from a PLC variable that records why the last run ended.

## Runs and their metadata

Analytics need to know what was tested. The web app's run setup form collects it before Start:

| Field | Example |
|---|---|
| Sample id | `PMP-2611-07` |
| Pump model and batch | `Model X, lot 2611` |
| Liquid and density | `Hand soap A, 1.03 g/mL` |
| Nominal output and tolerance | `1.00 mL ± 5%` |
| Priming strokes to exclude | `5` |
| Notes | free text |

The form creates a planned run. When the `run` start event arrives with a new `run_no`, the backend links it to the planned run. A run started locally at the rig gets a row with blank metadata that someone can fill in afterwards, so no data is lost.

## Database (proposed)

Alongside the existing `telemetry`, `gateway_status`, `commands` and `command_events` tables:

| Table | One row per | Key columns |
|---|---|---|
| `test_runs` | run | `machine_id`, `run_no` (unique together), `started_at`, `ended_at`, `end_reason`, `started_by` (user or `local`), `settings` (JSON), and the metadata above |
| `strokes` (hypertable on `ts`) | stroke | `machine_id`, `run_no`, `stroke_no` (unique together, so repeats are ignored), `mass_g`, `stroke_time_ms`, `stroke_setpoint_mm`, `flags` |

Volume is computed in a view, not stored. The data is small: one stroke a second for eight hours is under 30,000 rows a day. The continuous `telemetry` table is the larger one, which matters if the production cloud has a size cap (see [../log/topics/05-cloud-hosting.md](../log/topics/05-cloud-hosting.md)).

## Analytics

**Per stroke:** mass, volume, deviation from nominal in %, in or out of tolerance.

**Per run** (valid strokes only, priming strokes excluded):

| Metric | How | What it tells the client |
|---|---|---|
| Mean output | average volume | Is the pump delivering its rated dose |
| Standard deviation | sample std dev | Spread in mL |
| **CV %** | std dev ÷ mean × 100 | The headline consistency number, comparable across pump sizes |
| Min, max, range | | Worst strokes |
| % within tolerance | strokes inside the band ÷ n | Plain pass rate |
| Cp, Cpk | Cp = (USL − LSL) ÷ 6s; Cpk = min(USL − mean, mean − LSL) ÷ 3s | Capability against spec; needs about 30+ strokes to mean much |
| Drift | slope of volume against stroke number, per 100 strokes | Output creeping up or down as the pump wears or warms |
| Priming strokes | strokes until output stays within a set % of the run's steady mean | How fast a new pump primes |

**Across runs:** run means and CV over time; run-to-run comparison by sample, model or batch; a control chart of run means (individuals chart, limits at mean ± 2.66 × average moving range); output against the stroke setpoint, to see how the servo setting changes the dose.

### Run summary in SQL (sketch)

```sql
CREATE VIEW run_summary AS
WITH v AS (
  SELECT r.machine_id, r.run_no, r.sample_id, r.lsl_ml, r.usl_ml,
         s.stroke_no, s.mass_g / r.density_g_ml AS ml
  FROM test_runs r
  JOIN strokes s ON s.machine_id = r.machine_id AND s.run_no = r.run_no
  WHERE s.flags = 0 AND s.stroke_no > r.priming_strokes
)
SELECT machine_id, run_no, sample_id,
       count(*)                                   AS n,
       avg(ml)                                    AS mean_ml,
       stddev_samp(ml)                            AS sd_ml,
       100 * stddev_samp(ml) / avg(ml)            AS cv_pct,
       avg((ml BETWEEN lsl_ml AND usl_ml)::int) * 100 AS pct_in_spec,
       least(max(usl_ml) - avg(ml), avg(ml) - max(lsl_ml))
         / nullif(3 * stddev_samp(ml), 0)         AS cpk,
       regr_slope(ml, stroke_no) * 100            AS drift_ml_per_100
FROM v
GROUP BY machine_id, run_no, sample_id;
```

## Dashboard

| Section | Panels |
|---|---|
| Live | Gateway online/offline, mode, rig state, fault, run number, progress (strokes done of target), live weight, cup fill %, servo position, last stroke's volume |
| Current run | Stroke-by-stroke volume with the tolerance band, running mean and CV, histogram |
| Run history | Table of runs: sample, mean, CV %, Cpk, % in spec, drift, end reason; filter by sample, model, batch, date |
| Comparison | Spread per run side by side, control chart of run means, output against stroke setpoint |

Grafana covers the live view, time series, tables and histograms. Run setup, Start/Stop and setpoints live in the web app, and some comparison charts may be easier to build there too.

## To agree with the client

Nominal output and tolerance per pump type; how CV and Cpk should be reported; what counts as primed; whether runs are pass/fail and on what rule; which runs are compared with which.
