import { useState } from "react";
import PlantLoader from "../components/PlantLoader";
import { predictRelease } from "../lib/api";

const MATERIALS = ["Urea", "Hydroxyapatite", "KCl", "Zinc oxide"];
const NUTRIENT_NAMES = { N: "nitrogen", P: "phosphorus", K: "potassium" };

export default function Predict() {
  const [form, setForm] = useState({ fertilizer_material: "Urea", nutrient: "N", medium: "soil", temperature_C: 25 });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function run(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await predictRelease({ ...form, temperature_C: Number(form.temperature_C) });
      setResult(data);
    } catch {
      setError("Couldn't reach the prediction engine. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <h1>How fast will it release?</h1>
        <p>Describe the fertilizer and where it goes. We'll show the curve.</p>
      </section>

      <form className="card form" onSubmit={run}>
        <div className="field">
          <label htmlFor="mat">Material</label>
          <select id="mat" value={form.fertilizer_material} onChange={set("fertilizer_material")}>
            {MATERIALS.map((m) => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="nut">Nutrient</label>
          <select id="nut" value={form.nutrient} onChange={set("nutrient")}>
            <option value="N">Nitrogen</option>
            <option value="P">Phosphorus</option>
            <option value="K">Potassium</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="med">Where</label>
          <select id="med" value={form.medium} onChange={set("medium")}>
            <option value="soil">Soil</option>
            <option value="water">Water</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="tmp">Temperature (&deg;C)</label>
          <input id="tmp" type="number" value={form.temperature_C} onChange={set("temperature_C")} />
        </div>
        <button className="primary" disabled={loading} type="submit">
          {loading ? "Running\u2026" : "Predict release"}
        </button>
      </form>

      {loading && <div className="card result"><PlantLoader /></div>}

      {error && <div className="card result"><p>{error}</p></div>}

      {result && !loading && (
        <div className="card result">
          <div className="big">
            {result.t80_days_estimate ? `${Math.round(result.t80_days_estimate)} days` : "Beyond 60 days"}
          </div>
          <p className="sub">to release 80% of the {NUTRIENT_NAMES[form.nutrient]}</p>
        </div>
      )}
    </main>
  );
}