import { useEffect, useMemo, useState } from "react";
import { BRING_BACK, DEVICES, PHASES, type DeviceId, type Task } from "./data";

type IpKey = "PC_IP" | "LAPTOP_IP" | "IPC_IP";
interface Saved {
  done: Record<string, string>;
  ips: Record<IpKey, string>;
}

const KEY = "ipc-homelab-guide-v1";
const EMPTY: Saved = { done: {}, ips: { PC_IP: "", LAPTOP_IP: "", IPC_IP: "" } };

function load(): Saved {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return EMPTY;
    const s = JSON.parse(raw);
    return { done: s.done ?? {}, ips: { ...EMPTY.ips, ...(s.ips ?? {}) } };
  } catch {
    return EMPTY;
  }
}

const DEVICE = Object.fromEntries(DEVICES.map((d) => [d.id, d])) as Record<DeviceId, (typeof DEVICES)[number]>;
const ALL_TASKS = PHASES.flatMap((p) => p.tasks);

function fill(text: string, ips: Record<IpKey, string>) {
  return text.replace(/\{(PC_IP|LAPTOP_IP|IPC_IP)\}/g, (_, k: IpKey) => ips[k].trim() || k);
}

function Chip({ id }: { id: DeviceId }) {
  return <span className={`chip d-${id}`}>{DEVICE[id].short}</span>;
}

function CopyButton({ text }: { text: string }) {
  const [state, setState] = useState<"idle" | "ok" | "fail">("idle");
  return (
    <button
      type="button"
      className="copy"
      onClick={(e) => {
        const pre = (e.currentTarget.parentElement?.querySelector("pre") ?? null) as HTMLElement | null;
        navigator.clipboard
          .writeText(text)
          .then(() => setState("ok"))
          .catch(() => {
            if (pre) {
              const r = document.createRange();
              r.selectNodeContents(pre);
              const sel = window.getSelection();
              sel?.removeAllRanges();
              sel?.addRange(r);
            }
            setState("fail");
          })
          .finally(() => setTimeout(() => setState("idle"), 1800));
      }}
    >
      {state === "ok" ? "Copied" : state === "fail" ? "Selected, press Ctrl+C" : "Copy"}
    </button>
  );
}

function Diagram() {
  return (
    <div className="diagram-scroll">
      <svg className="diagram" viewBox="0 0 900 330" role="img" aria-labelledby="dg-t dg-d">
        <title id="dg-t">How the home-lab devices connect</title>
        <desc id="dg-d">
          The spare laptop runs the simulated PLC on port 5020. The BX-220 gateway reads it over Modbus TCP and publishes to
          the MQTT broker on this PC, port 1883. On this PC the ingest service writes to TimescaleDB and Grafana draws the
          dashboard for your browser. The KV-8000 can later replace the laptop.
        </desc>
        <defs>
          <marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M1 1L9 5L1 9" fill="none" stroke="context-stroke" strokeWidth="1.6" />
          </marker>
        </defs>

        <g className="node d-laptop">
          <rect x="20" y="58" width="180" height="84" rx="4" />
          <text x="34" y="84" className="n-eyebrow">SPARE LAPTOP</text>
          <text x="34" y="106" className="n-title">Simulated PLC</text>
          <text x="34" y="127" className="n-sub">listens on :5020</text>
        </g>
        <g className="node d-kv dashed">
          <rect x="20" y="212" width="180" height="76" rx="4" />
          <text x="34" y="238" className="n-eyebrow">LATER</text>
          <text x="34" y="259" className="n-title">KV-8000</text>
          <text x="34" y="278" className="n-sub">Host Link :8501</text>
        </g>

        <g className="node d-ipc">
          <rect x="300" y="58" width="180" height="84" rx="4" />
          <text x="314" y="84" className="n-eyebrow">CONTEC BX-220</text>
          <text x="314" y="106" className="n-title">Edge gateway</text>
          <text x="314" y="127" className="n-sub">connects out only</text>
        </g>

        <g className="container d-pc">
          <rect x="560" y="14" width="326" height="302" rx="6" />
          <text x="576" y="40" className="n-eyebrow">THIS PC · DOCKER</text>
        </g>
        <g className="node inner">
          <rect x="576" y="58" width="134" height="56" rx="3" />
          <text x="590" y="82" className="n-title s">MQTT broker</text>
          <text x="590" y="101" className="n-sub">:1883</text>
        </g>
        <g className="node inner">
          <rect x="736" y="58" width="134" height="56" rx="3" />
          <text x="750" y="82" className="n-title s">Ingest</text>
          <text x="750" y="101" className="n-sub">MQTT → rows</text>
        </g>
        <g className="node inner">
          <rect x="736" y="148" width="134" height="56" rx="3" />
          <text x="750" y="172" className="n-title s">TimescaleDB</text>
          <text x="750" y="191" className="n-sub">:5432, local</text>
        </g>
        <g className="node inner">
          <rect x="576" y="148" width="134" height="56" rx="3" />
          <text x="590" y="172" className="n-title s">Grafana</text>
          <text x="590" y="191" className="n-sub">:3000</text>
        </g>
        <g className="node inner">
          <rect x="576" y="238" width="294" height="56" rx="3" />
          <text x="590" y="262" className="n-title s">Your browser</text>
          <text x="590" y="281" className="n-sub">http://localhost:3000</text>
        </g>

        <line className="wire" x1="298" y1="100" x2="204" y2="100" markerEnd="url(#ah)" markerStart="url(#ah)" />
        <text x="251" y="90" className="w-label" textAnchor="middle">Modbus TCP</text>
        <text x="251" y="120" className="w-label m" textAnchor="middle">every 1 s</text>

        <line className="wire" x1="482" y1="86" x2="572" y2="86" markerEnd="url(#ah)" markerStart="url(#ah)" />
        <text x="527" y="76" className="w-label" textAnchor="middle">MQTT</text>
        <text x="527" y="106" className="w-label m" textAnchor="middle">data up,</text>
        <text x="527" y="121" className="w-label m" textAnchor="middle">commands</text>
        <text x="527" y="136" className="w-label m" textAnchor="middle">down</text>

        <path className="wire dashed" d="M204 250 H390 V146" fill="none" markerEnd="url(#ah)" />

        <line className="wire thin" x1="712" y1="86" x2="732" y2="86" markerEnd="url(#ah)" />
        <line className="wire thin" x1="803" y1="116" x2="803" y2="144" markerEnd="url(#ah)" />
        <line className="wire thin" x1="734" y1="176" x2="714" y2="176" markerEnd="url(#ah)" />
        <line className="wire thin" x1="643" y1="206" x2="643" y2="234" markerEnd="url(#ah)" />
      </svg>
    </div>
  );
}

const READ_FLOW: { d: DeviceId; t: string }[] = [
  { d: "laptop", t: "The simulated PLC keeps machine values in Modbus registers. Holding register 100 is motor speed, coil 0 is running or not." },
  { d: "ipc", t: "Every second the gateway reads each register in its tag map, then scales it (101 × 0.1 = amps) and names it (103: 1 → REMOTE)." },
  { d: "ipc", t: "It publishes one JSON message with a UTC timestamp and a sequence number to factory/plant-a/press-01/telemetry. If the broker is down, it keeps up to 10,000 messages in memory and sends them later." },
  { d: "pc", t: "The ingest service receives the message and writes one database row per value into TimescaleDB." },
  { d: "pc", t: "Grafana queries the database every 5 seconds and redraws the dashboard in your browser." },
];

const WRITE_FLOW: { d: DeviceId; t: string }[] = [
  { d: "pc", t: "You send motor_start (today with send_command.py, later with a button). It carries a unique id and expires 10 seconds after it's sent." },
  { d: "pc", t: "The ingest service records it in the commands table. That's your audit log of who asked for what." },
  { d: "ipc", t: "The gateway checks it: is the command on the allowlist, not expired, not a repeat, and is the machine in REMOTE mode? It replies accepted, rejected or expired." },
  { d: "ipc", t: "If accepted, it pulses coil 10 on the PLC for half a second, then replies executed." },
  { d: "laptop", t: "The PLC makes the final call. It starts the motor only if its own rules allow it, and the dashboard shows Running once the next reading arrives." },
  { d: "laptop", t: "Every 2 seconds the gateway bumps a heartbeat register. If that stops for 6 seconds, the PLC stops the motor by itself. The real E-stop is wired directly and never goes through any of this." },
];

function Flow({ title, lede, steps }: { title: string; lede: string; steps: { d: DeviceId; t: string }[] }) {
  return (
    <div className="flow">
      <h3>{title}</h3>
      <p className="muted">{lede}</p>
      <ol>
        {steps.map((s, i) => (
          <li key={i}>
            <Chip id={s.d} />
            <span>{s.t}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function TaskRow({
  task, done, open, onToggle, onOpen, ips,
}: {
  task: Task; done?: string; open: boolean; onToggle: (v: boolean) => void; onOpen: () => void; ips: Record<IpKey, string>;
}) {
  const hasDetail = !!(task.steps?.length || task.code || task.done);
  const code = task.code ? fill(task.code, ips) : "";
  return (
    <li className={`task${done ? " is-done" : ""}${task.hold ? " is-hold" : ""}`}>
      <input id={`t-${task.id}`} type="checkbox" checked={!!done} onChange={(e) => onToggle(e.target.checked)} />
      <div className="task-body">
        <label htmlFor={`t-${task.id}`} className="task-title">
          {task.hold && <span className="hold">Hold point</span>}
          {task.title}
        </label>
        <div className="task-meta">
          {task.devices.map((d) => <Chip key={d} id={d} />)}
          {done && <span className="when">done {new Date(done).toLocaleDateString(undefined, { day: "numeric", month: "short" })}</span>}
        </div>
        <p className="why">{task.why}</p>
        {hasDetail && (
          <button type="button" className="more" aria-expanded={open} onClick={onOpen}>
            {open ? "Hide steps" : "Show steps"}
          </button>
        )}
        {open && hasDetail && (
          <div className="detail">
            {task.steps && (
              <ul className="steps">
                {task.steps.map((s, i) => <li key={i}>{fill(s, ips)}</li>)}
              </ul>
            )}
            {code && (
              <div className="code">
                <pre>{code}</pre>
                <CopyButton text={code} />
              </div>
            )}
            {task.done && (
              <p className="done-when"><span>Done when</span>{fill(task.done, ips)}</p>
            )}
          </div>
        )}
      </div>
    </li>
  );
}

export default function App() {
  const [saved, setSaved] = useState<Saved>(load);
  const [filter, setFilter] = useState<DeviceId | "all">("all");
  const [hideDone, setHideDone] = useState(false);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [confirmReset, setConfirmReset] = useState(false);

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch { /* storage unavailable: ticks last for this visit only */ }
  }, [saved]);

  const counts = useMemo(() => {
    const c: Record<string, [number, number]> = { all: [0, 0] };
    for (const d of DEVICES) c[d.id] = [0, 0];
    for (const t of ALL_TASKS) {
      const isDone = saved.done[t.id] ? 1 : 0;
      c.all[0] += isDone; c.all[1] += 1;
      for (const d of t.devices) { c[d][0] += isDone; c[d][1] += 1; }
    }
    return c;
  }, [saved.done]);

  const allOpen = ALL_TASKS.every((t) => open[t.id]);
  const toggle = (id: string, v: boolean) =>
    setSaved((s) => {
      const done = { ...s.done };
      if (v) done[id] = new Date().toISOString(); else delete done[id];
      return { ...s, done };
    });
  const nextTask = ALL_TASKS.find((t) => !saved.done[t.id] && !PHASES.find((p) => p.tasks.includes(t))?.later);
  const pct = Math.round((counts.all[0] / counts.all[1]) * 100);

  return (
    <div className="wrap">
      <header className="hero">
        <p className="eyebrow">ipc_connection · home lab</p>
        <h1>IPC Home Lab Guide</h1>
        <p className="lede">
          Three machines at home stand in for a factory and the cloud. This page explains what each one does, how data and commands
          move between them, and then lists every setup task in order, tagged with the machine you do it on.
        </p>
        <div className="legend" aria-label="Device colours">
          {DEVICES.map((d) => <Chip key={d.id} id={d.id} />)}
          <span className="muted small">Each task is tagged with the machines it touches.</span>
        </div>
      </header>

      <section aria-labelledby="h-devices">
        <h2 id="h-devices"><span className="num">1</span>The machines and their jobs</h2>
        <p className="section-lede">
          Enter each machine's IP address once. The commands in the checklist fill them in for you, and they're saved in this browser.
        </p>
        <div className="devices">
          {DEVICES.map((d) => (
            <article key={d.id} className={`device d-${d.id}`}>
              <div className="device-head">
                <h3>{d.name}</h3>
                <p className="role">{d.role}</p>
              </div>
              <ul className="runs">{d.runs.map((r, i) => <li key={i}>{r}</li>)}</ul>
              <dl>
                <dt>Network</dt><dd>{d.ports}</dd>
                <dt>At the plant</dt><dd>{d.plant}</dd>
              </dl>
              {d.ipKey ? (
                <div className="ip">
                  <label htmlFor={`ip-${d.id}`}>{d.ipKey}</label>
                  <input
                    id={`ip-${d.id}`}
                    inputMode="decimal"
                    placeholder="e.g. 192.168.1.20"
                    value={saved.ips[d.ipKey]}
                    onChange={(e) => {
                      const k = d.ipKey as IpKey;
                      setSaved((s) => ({ ...s, ips: { ...s.ips, [k]: e.target.value } }));
                    }}
                  />
                </div>
              ) : (
                <p className="ip-none muted small">No address needed until the KV-8000 session.</p>
              )}
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="h-map">
        <h2 id="h-map"><span className="num">2</span>How they connect</h2>
        <p className="section-lede">
          Only two connections cross the network: the gateway reaching out to the PLC, and the gateway reaching out to the broker.
          Everything else happens inside this PC. That's why the firewall rules are on the laptop (port 5020) and this PC (port 1883), and none on the IPC.
        </p>
        <Diagram />
      </section>

      <section aria-labelledby="h-flow">
        <h2 id="h-flow"><span className="num">3</span>What actually happens</h2>
        <div className="flows">
          <Flow title="One reading, PLC to dashboard" lede="Runs every second, about a second end to end." steps={READ_FLOW} />
          <Flow title="One command, button to motor" lede="The cloud only asks. The PLC decides." steps={WRITE_FLOW} />
        </div>
      </section>

      <section aria-labelledby="h-list">
        <h2 id="h-list"><span className="num">4</span>Checklist</h2>
        <p className="section-lede">
          Work top to bottom: later phases depend on earlier ones. Amber items are hold points, so stop and check before going past them.
          Ticks save in this browser and work offline.
        </p>

        <div className="progress-card">
          <div className="progress-top">
            <strong>{counts.all[0]} of {counts.all[1]} done</strong>
            <span className="muted">{pct}%</span>
          </div>
          <div className="bar" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}>
            <i style={{ width: `${pct}%` }} />
          </div>
          {nextTask && (
            <p className="next">
              <span>Next up</span>
              <a href={`#t-${nextTask.id}`}>{nextTask.title}</a>
              {nextTask.devices.map((d) => <Chip key={d} id={d} />)}
            </p>
          )}
        </div>

        <div className="filters" role="group" aria-label="Show tasks for">
          {(["all", ...DEVICES.map((d) => d.id)] as const).map((f) => (
            <button
              key={f}
              type="button"
              className={`filter${filter === f ? " on" : ""}${f !== "all" ? ` d-${f}` : ""}`}
              aria-pressed={filter === f}
              onClick={() => setFilter(f)}
            >
              {f === "all" ? "All machines" : DEVICE[f].short}
              <span className="count">{counts[f][0]}/{counts[f][1]}</span>
            </button>
          ))}
          <span className="spacer" />
          <label className="switch">
            <input id="hide-done" type="checkbox" checked={hideDone} onChange={(e) => setHideDone(e.target.checked)} />
            Hide done
          </label>
          <button
            type="button"
            className="link"
            onClick={() => setOpen(allOpen ? {} : Object.fromEntries(ALL_TASKS.map((t) => [t.id, true])))}
          >
            {allOpen ? "Collapse all steps" : "Expand all steps"}
          </button>
        </div>

        {PHASES.map((p, pi) => {
          const tasks = p.tasks.filter(
            (t) => (filter === "all" || t.devices.includes(filter)) && !(hideDone && saved.done[t.id]),
          );
          if (!tasks.length) return null;
          const pd = p.tasks.filter((t) => saved.done[t.id]).length;
          return (
            <div key={p.id} className={`phase${pd === p.tasks.length ? " complete" : ""}${p.later ? " later" : ""}`}>
              <div className="phase-head">
                <span className="phase-num">{String(pi + 1).padStart(2, "0")}</span>
                <h3>{p.title}{p.later && <span className="tag">later</span>}</h3>
                <span className="phase-count">{pd}/{p.tasks.length}</span>
                <p>{p.intro}</p>
              </div>
              <ul className="tasks">
                {tasks.map((t) => (
                  <TaskRow
                    key={t.id}
                    task={t}
                    done={saved.done[t.id]}
                    open={!!open[t.id]}
                    ips={saved.ips}
                    onToggle={(v) => toggle(t.id, v)}
                    onOpen={() => setOpen((o) => ({ ...o, [t.id]: !o[t.id] }))}
                  />
                ))}
              </ul>
            </div>
          );
        })}
        {filter !== "all" && hideDone && counts[filter][0] === counts[filter][1] && (
          <p className="empty">Everything for {DEVICE[filter].name} is done.</p>
        )}
      </section>

      <section aria-labelledby="h-back" className="bring">
        <h2 id="h-back"><span className="num">5</span>Bring these back to Claude</h2>
        <ul>{BRING_BACK.map((b, i) => <li key={i}>{b}</li>)}</ul>
      </section>

      <footer>
        <p className="muted small">
          Ticks and IP addresses are stored only in this browser on this device. Opening the page on another machine starts fresh.
        </p>
        {confirmReset ? (
          <div className="confirm">
            <span>Clear every tick and IP address?</span>
            <button type="button" className="danger" onClick={() => { setSaved(EMPTY); setConfirmReset(false); }}>Clear</button>
            <button type="button" className="link" onClick={() => setConfirmReset(false)}>Cancel</button>
          </div>
        ) : (
          <button type="button" className="link" onClick={() => setConfirmReset(true)}>Reset checklist</button>
        )}
      </footer>
    </div>
  );
}
