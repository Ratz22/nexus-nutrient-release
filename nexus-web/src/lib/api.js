// Single place that talks to the backend. Pages never call fetch directly.
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";

export async function predictRelease(payload) {
  const r = await fetch(`${BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`Prediction failed (${r.status})`);
  return r.json();
}

export const SAMPLE_RUNS = [
  { id: "r1", when: "2026-10-20 14:32", material: "Urea", medium: "Soil", temp: 25, t80: 14.2 },
  { id: "r2", when: "2026-10-19 11:05", material: "Hydroxyapatite", medium: "Water", temp: 30, t80: 31.8 },
  { id: "r3", when: "2026-10-17 09:48", material: "KCl", medium: "Soil", temp: 20, t80: 62.0 },
];

export const SAMPLE_PLATES = [
  { id: "p1", title: "Dissolution, 30 \u00B0C", ar: "4/3" },
  { id: "p2", title: "Column leaching", ar: "1/1" },
  { id: "p3", title: "Particle size, TEM", ar: "3/4" },
  { id: "p4", title: "Release profile", ar: "16/10" },
  { id: "p5", title: "Soil core, day 14", ar: "4/5" },
  { id: "p6", title: "Chitosan coating", ar: "1/1" },
];

export const SAMPLE_FILES = [
  { id: "f1", name: "lab_run_oct.csv", rows: 184, added: "2026-10-18" },
  { id: "f2", name: "urea_soil_columns.csv", rows: 96, added: "2026-10-12" },
];