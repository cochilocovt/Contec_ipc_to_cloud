# ETO & Dose Tester: machine-file review

Reviewed 2026-11-13. This is a requirements assessment, not an implemented or commissioned machine program. It covers PLC/HMI work and the IPC/cloud integration. No machine files, gateway code, home-lab settings or services were changed.

## Source and inspection boundary

Source folder: `V:\VEEMAP\eto & test simulation\13.EVT-TM-27-0256_ETO & Dose Tester`. The supplied path duplicated this same folder.

Recursive inventory: 373 files, 213,888,842 bytes: 250 SolidWorks parts, 45 assemblies, 56 drawings, 5 STEP files, 4 PDFs, 1 PPTX, 4 JPGs, 1 PNG and 7 thumbnail databases. Inventory includes a small SolidWorks owner file; it was left untouched.

Read all four PDFs and all four slide texts; visually inspected the machine layout, proposal layout, both instrument purchase orders and customer images. Inventoried CAD/support folders. Did not open/rebuild the native SolidWorks assembly, resolve active/suppressed components, check interference or establish which legacy models are actually used. No existing Graphify graph was present; no graph was generated for this bounded assessment.

No PLC/HMI project, electrical schematic, I/O schedule, test acceptance specification or software source was identified in the inventory. The files present are CAD, presentation, PDF and image formats. No installed hardware, wiring, PLC connection, calibration, motion or test result was checked.

| Evidence | What it establishes |
|---|---|
| `Proposal ETO & Dose Tester.pdf`, pages 1–3; corresponding PPTX slides | TRIMAS proposal dated 24 Apr 2026; SMC pressing axis; upper Unipulse load cell; lower Unipulse load cell for dose checking; SS container; Keyence VT5-X12 HMI; foldable HMI option |
| `ETO & Dose Tester.pdf`, page 1 | Pressing-unit drawing dated 23 Apr 2026; envelope 340 × 288 × 508 mm; top press, bottle fixture and separate receiving cup |
| `BOM & DOCUMENTS/P.O. 26-27-PVT-155-PJ0256_UNIPULSE.pdf`, page 1 | Order dated 23 May 2026: one UCW2-20N, 20 N; one UNLRS-100N, 100 N. An order is not proof of delivered/installed hardware |
| `BOM & DOCUMENTS/P.O. 26-27-PVT-154-PJ0256_BURSTER.pdf`, page 1 | Same-date order: one 9236-V200, two strain-gauge input channels, two analog outputs printed as `0…±10VDC`, accuracy printed as 0.1% F.S., DIN rail mounting. Confirm actual output configuration/range; extracted text loses the ± symbol |
| `Customer Part/Screenshot 2026-06-04 093123.png` | Customer states bottle/pump open height 90–270 mm; maximum oval/rectangular bottle size 110 mm; minimum circular diameter 30 mm |
| `Customer Part/image001.jpg`, `image002.jpg`, `image003.jpg` | Bottle/pump reference photos; these are not calibrated dimensional measurements or dose specifications |
| `stand/UCW2-20N.SLDPRT`, `stand/UNLRS- 100N.SLDPRT`; `KEYENCE/VT5-X12.SLDASM` | Matching sensor/HMI model names exist in CAD; active assembly membership was not established |

Source SHA-256:

```text
ETO & Dose Tester.pdf
8b42e26ac6c311a5aea3fcd22ab0863384946b4851dd3b0f5835c139f265e5b5
Proposal ETO & Dose Tester.pdf
98b253bac0a23c967bb330ebd7f73d52e4ec6c621fdc7247c07af4b10c81c89a
Proposal ETO & Dose Tester.pptx
467971ae2ab04b4b5d89cdbbf1a2c7e9ade77b0649bbccbd45d1585265e56711
P.O. 26-27-PVT-154-PJ0256_BURSTER.pdf
3f561d550971d7e0b3b126fa9abf5f32c53ad8faac0d35a9f74ae8f786659d9e
P.O. 26-27-PVT-155-PJ0256_UNIPULSE.pdf
121f9b097a0e1599b23efce0bb437c2e17a9cb191ce49276c5e877b790b035b5
```

No commercial terms, prices, payment details or personal contact details are reproduced here.

## What the machine appears intended to do

This is a combined pressing-force and dispensed-dose tester. The upper axis presses a pump while measuring the operating force; the lower receiving cup measures the dispensed material. ETO plausibly means effort to operate in this context, but neither its expansion nor the exact acceptance metric is defined in the supplied documents.

Proposed sensor assignment: 100 N upper force channel and 20 N lower weighing channel. The proposal establishes upper/lower functions and the PO establishes capacities, but neither explicitly maps each ordered model to its installed position. Confirm wiring and mounting before assigning channels.

The 90–270 mm sample height range requires a verified setup method for different bottles. It does not establish the actuator travel. CAD filenames include SMC LEFS/LEKFS/JXC models, Mitsubishi HG-KN13J/MR-JE-10CA and FX5U models, plus older machine-number assemblies. Their presence cannot establish the selected actuator, drive, PLC or communication interface. The existing KV-X310 requirement remains prior owner context; this folder does not independently confirm the installed CPU.

## Required program changes

The earlier design in this directory concentrated on dose consistency. Add force measurement and treat each completed stroke as one synchronized test result with both force and dose quality. Values, names and states below are proposals until agreed with the PLC programmer.

| Layer | Required change | Dependency / reason |
|---|---|---|
| Electrical / PLC analog input | Identify two compatible analog input channels; record raw counts, range, polarity, scaling, zero, calibration revision and channel validity | Amplifier outputs are analog. Do not assume a digital weighing protocol, ADC resolution or channel mapping |
| PLC force acquisition | Acquire force during the press, synchronize with actual position/time, calculate the agreed ETO metric, retain peak force and its position if required | One-second cloud polling cannot establish a transient peak. Choose acquisition rate from measured stroke dynamics and amplifier/input bandwidth; no rate is specified here |
| PLC dose acquisition | Capture stable pre-dose and post-dose cup readings; calculate net dose; handle settling timeout, dripping, priming, negative delta, saturation and cup removal/full conditions | A live weight reading is not a completed dose measurement. Fixed delays alone need validation |
| PLC sequence | Define ready/setup/priming/press/return/settle/result/complete/stopping/fault behavior; ensure each cycle gets exactly one result or an explicit invalid result | Sequence is absent from the proposal. Distinguish zero dose from an invalid reading |
| PLC recipes | Bound contact/start position, press travel, down/return speed, dwell, stroke count, interval, force limit, settling criteria and prime count as applicable | Actual axis capability, geometry and approved operating limits are still unknown; reject out-of-range values |
| PLC interlocks | Enforce motion limits, servo ready/homed, force overload, measurement validity, cup/sample presence and guard/E-stop behavior as applicable | Identify real sensors and safety circuit first. The PLC owns motion; a measured force limit does not replace a safety function |
| PLC results interface | Publish coherent completed records with session/run/stroke identity, sequence, recipe revision, force result, dose result, status flags and timestamps | Need a buffer handshake, overwrite/gap detection, restart identity and validity markers so partial records are never treated as complete |
| Local HMI | Use the proposed VT5-X12 for setup, live force/weight/position, recipes, run progress, results and alarms; separate operator, setup and calibration access | Confirm actual HMI/project and authority arbitration between local HMI and remote client |
| Gateway protocol / configuration | Add the agreed KV-X310 protocol if that CPU is confirmed; use verified PLC node/register definitions for both channels and results | Current `config.py` rejects everything except Modbus TCP and `plc.py` is a Modbus client. Prior OPC UA choice remains a proposal pending actual PLC configuration |
| Gateway commands | Add named bounded recipe/setpoint requests, state/freshness checks and PLC apply/reject/active-value confirmation | Current `Command` and `Plc.execute()` only implement configured fixed writes/pulses; `params.value` is not implemented. Keep command ID, expiry, allowlist and plant approval rules |
| Gateway reliability | Persist completed results and read cursor; replay with database idempotency; distinguish a broker publish from durable result storage | Current `app.py` uses a bounded in-memory deque for telemetry only. It is not a durable test-result journal and can drop old telemetry or lose it on restart |
| Contract / cloud | Extend the contract with completed stroke and run events; ingest them; add run/stroke/recipe/calibration records using reviewed migrations | Existing ingest subscribes only to telemetry/status/cmd/ack; schema has no test-run or stroke tables. Use session-safe IDs and include site in identity where needed |
| Dashboard / reports | Show force and dose together per stroke; separate pass/fail limits, invalid readings, priming exclusions, force trends and dose consistency | Store force in N, net dose in g, derived volume in mL only with recorded density. Add force-versus-position curves only if agreed and acquired at adequate resolution |
| Remote web app | Provide authenticated run setup, approved controls, bounded setting changes and audit history; show active PLC settings and confirmed state | Local and remote clients must not race. Machine motion/homing/jog/calibration remains local unless separately designed and approved |

Likely sequence for discussion: verify setup → tare unloaded force channel and cup under approved conditions → prime as required → record stable cup baseline → press while acquiring force/position → return → wait for valid settled dose → finalize force/dose record → repeat or finish. This is a proposed sequence, not a recovered machine specification. Force and dose checks may be separate test modes if the client requires them.

Suggested minimum completed-record content: machine/site, boot or test-session identity, run/stroke ID, sequence, recipe ID/revision, force peak in N, force metric validity, net dose in g, dose validity, actual travel/time, calibration references, priming flag and invalid/abort reason. Curve data needs its own agreed sampling, storage and retention design. Do not infer an entire force curve from a peak scalar.

## Measurement feasibility must be checked before promising accuracy

Force capacity is not weighing resolution. Using standard gravity only as an illustration, 20 N corresponds to about 2.04 kg total supported mass; that includes cup/platform preload and dispensed liquid, subject to mounting and the manufacturer's limits. Taring removes an offset from the reading, not physical load from the sensor.

If the dose signal is configured so that 20 N spans the full measurement range, 0.1% of that range is 0.02 N, about 2.04 g equivalent. This is a conditional interpretation of the PO's F.S. accuracy, not a measured error or a vendor-confirmed error budget. It does not establish repeatability, ADC resolution, effective noise or the uncertainty of a difference measurement. For a small dose, the suitability of this chain is a priority question. Verify actual gain/range, load-cell certificates, amplifier specifications, analog input accuracy/resolution, filtering and whole-system repeatability at the required dose. A digital interface alone would not fix an unsuitable sensor/amplifier accuracy.

For gravimetric volume, `dose_mL = net_mass_g / density_g_per_mL`; record the liquid and applicable density/temperature conditions. No nominal dose, allowed error, required force accuracy or pass/fail rule was supplied. A CAD filename mentioning 2 cc is not an approved nominal dose.

## Contradictions and missing information

1. Drawing envelope is 340 × 288 × 508 mm; proposal is 340 × 290 × 510 mm. Obtain the released assembly/revision; neither value sets program travel limits.
2. Proposal slide/page 4 mentions four cameras and a missing next slide. No corresponding inspection sequence/specification is provided. Treat this as unresolved scope; do not add vision inspection on that sentence alone.
3. Confirm installed PLC CPU, expansion modules, axis/controller/drive and communication wiring. Obtain electrical schematic, I/O list, PLC and HMI projects, firmware/project versions and backups.
4. Confirm sensor assignment, installed amplifier output range and analog wiring/configuration, actual calibration and required dose/force uncertainty.
5. Agree the ETO definition (peak, breakaway, average, curve features or another metric), test speed/travel and force/dose limits per pump recipe. Clarify simultaneous versus separate ETO/dose modes.
6. Confirm the bottle-height adjustment method, contact detection, available travel, mechanical stops and safe permitted stroke for each sample fixture.
7. Agree priming, settling, dripping, cup capacity/emptying, abort/restart rules and traceable sample/run identity.
8. Confirm guards, E-stop circuit, presence/limit sensors, local/remote arbitration and permitted behavior on gateway/cloud/PLC link loss. Existing remote-control approval remains required.

## Implementation order and acceptance

1. Freeze the actual hardware/electrical list and approved test specification; resolve measurement feasibility first.
2. Commission both channels locally with traceable force/weight checks; confirm polarity, repeatability, drift, saturation and usable range.
3. Implement and test the local PLC sequence and HMI; verify overload, travel limits, unsettled dose, cup removal/full, drive fault and interrupted-cycle behavior.
4. Agree versioned PLC records and command handshakes; add a read-only machine profile/driver and simulator for force plus dose. Keep the existing home-lab profile separate.
5. Add durable result capture, cloud schema/ingest and reports; prove restart/reconnect replay, duplicate suppression, consistent records and explicit buffer-overrun gaps.
6. Add approved remote recipe/start/stop requests only after local acceptance. Test role checks, invalid/nonfinite values, stale state, expiry, duplicate delivery, local-mode refusal, PLC rejection and telemetry confirmation. Keep `control.enabled: false` until plant approval.

This session changed documentation only. No functional acceptance or hardware accuracy is claimed.
