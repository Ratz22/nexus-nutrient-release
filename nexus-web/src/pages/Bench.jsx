import { useState } from "react";
import { SAMPLE_RUNS, SAMPLE_PLATES, SAMPLE_FILES } from "../lib/api";
import Marquee from "../components/Marquee";

const TABS = ["Runs", "Plates", "Data"];

export default function Bench() {
  const [tab, setTab] = useState("Runs");
  const [files, setFiles] = useState(SAMPLE_FILES);

  const runs = SAMPLE_RUNS;
  const latest = runs[0];
  const avg = (runs.reduce((s, r) => s + r.t80, 0) / runs.length).toFixed(1);

  return (
    <>
      <main className="page">
        <section className="hero">
          <h1>Bench</h1>
          <p>Everything you've run, in one place.</p>
        </section>

        <div className="summary">
          <div className="card"><div className="label">Runs</div><div className="value">{runs.length}</div></div>
          <div className="card"><div className="label">Average to 80%</div><div className="value">{avg} d</div></div>
          <div className="card"><div className="label">Files</div><div className="value">{files.length}</div></div>
        </div>

        <div className="tabs" role="tablist">
          {TABS.map((t) => (
            <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
              {t}
            </button>
          ))}
        </div>

        {tab === "Runs" && (
          <div className="bento">
            <div className="card span-8">
              <div className="label">Latest</div>
              <div className="value">{latest.material}</div>
              <p style={{ marginTop: 8 }}>{latest.medium} &middot; {latest.temp} &deg;C &middot; {latest.when}</p>
              <p style={{ marginTop: 20, fontSize: 28, color: "var(--accent)", fontWeight: 600 }}>80% in {latest.t80} days</p>
            </div>
            <div className="span-4 stack">
              {runs.slice(1).map((r) => (
                <div className="card" key={r.id}>
                  <div className="label">{r.when}</div>
                  <div className="card-title">{r.material}</div>
                  <p>80% in {r.t80} days</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "Plates" && (
          <div className="plates">
            {SAMPLE_PLATES.map((p) => (
              <div className="plate" key={p.id} style={{ "--ar": p.ar }}>
                <span>{p.title}</span>
              </div>
            ))}
          </div>
        )}

        {tab === "Data" && (
          <div className="card">
            {files.length === 0 && <p>No files yet. Upload a CSV from Fit to see it here.</p>}
            {files.map((f) => (
              <div className="row" key={f.id}>
                <div>
                  <div className="card-title">{f.name}</div>
                  <p className="small">{f.added}</p>
                </div>
                <div className="row-actions">
                  <span className="chip">{f.rows} rows</span>
                  <button className="danger" onClick={() => setFiles(files.filter((x) => x.id !== f.id))}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
      <Marquee runs={runs} />
    </>
  );
}