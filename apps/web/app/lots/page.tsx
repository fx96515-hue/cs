"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "../../lib/api";

type Lot = {
  id: number;
  cooperative_id: number;
  name: string;
  crop_year?: number | null;
  incoterm?: string | null;
  price_per_kg?: number | null;
  currency?: string | null;
  weight_kg?: number | null;
  expected_cupping_score?: number | null;
};

export default function LotsPage() {
  const [lots, setLots] = useState<Lot[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<any>({
    cooperative_id: "",
    name: "",
    crop_year: "",
    incoterm: "FOB",
    price_per_kg: "",
    currency: "USD",
    weight_kg: "",
    expected_cupping_score: "",
  });

  const load = () =>
    apiFetch<Lot[]>("/lots?limit=200")
      .then(setLots)
      .catch((e) => setErr(e.message));

  useEffect(() => {
    load();
  }, []);

  async function createLot() {
    setErr(null);
    setCreating(true);
    try {
      const payload: any = {
        cooperative_id: Number(form.cooperative_id),
        name: String(form.name || "").trim(),
        incoterm: form.incoterm || null,
        currency: form.currency || null,
      };
      if (!payload.name) throw new Error("Name fehlt");
      if (!payload.cooperative_id) throw new Error("cooperative_id fehlt");

      if (form.crop_year) payload.crop_year = Number(form.crop_year);
      if (form.price_per_kg) payload.price_per_kg = Number(form.price_per_kg);
      if (form.weight_kg) payload.weight_kg = Number(form.weight_kg);
      if (form.expected_cupping_score) payload.expected_cupping_score = Number(form.expected_cupping_score);

      await apiFetch<Lot>("/lots", { method: "POST", body: JSON.stringify(payload) });
      setForm({ cooperative_id: "", name: "", crop_year: "", incoterm: "FOB", price_per_kg: "", currency: "USD", weight_kg: "", expected_cupping_score: "" });
      load();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <h1>Lots</h1>
      {err && <div style={{ color: "crimson" }}>{err}</div>}

      <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 12, marginBottom: 16 }}>
        <b>Neues Lot</b>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, marginTop: 10 }}>
          <input placeholder="cooperative_id" value={form.cooperative_id} onChange={(e) => setForm({ ...form, cooperative_id: e.target.value })} />
          <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input placeholder="Erntejahr" value={form.crop_year} onChange={(e) => setForm({ ...form, crop_year: e.target.value })} />
          <input placeholder="Incoterm (FOB/CIF…)" value={form.incoterm} onChange={(e) => setForm({ ...form, incoterm: e.target.value })} />
          <input placeholder="Preis/kg" value={form.price_per_kg} onChange={(e) => setForm({ ...form, price_per_kg: e.target.value })} />
          <input placeholder="Währung" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
          <input placeholder="Gewicht (kg)" value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: e.target.value })} />
          <input placeholder="Erwarteter SCA-Score" value={form.expected_cupping_score} onChange={(e) => setForm({ ...form, expected_cupping_score: e.target.value })} />
        </div>
        <button
          onClick={createLot}
          disabled={creating}
          style={{ marginTop: 10, padding: "8px 12px", borderRadius: 8, border: "1px solid #eee", background: "white", cursor: "pointer" }}
        >
          {creating ? "Speichern…" : "Lot anlegen"}
        </button>
        <div style={{ fontSize: 12, color: "#555", marginTop: 6 }}>
          Hinweis: cooperative_id bekommst du aus der Kooperativen-Liste.
        </div>
      </div>

      {lots.length === 0 ? (
        <div>Keine Lots vorhanden.</div>
      ) : (
        <ul>
          {lots.map((l) => (
            <li key={l.id} style={{ marginBottom: 8 }}>
              <Link href={`/lots/${l.id}`}>{l.name}</Link>
              <div style={{ fontSize: 12, color: "#555" }}>
                Koop #{l.cooperative_id}
                {l.crop_year ? ` — ${l.crop_year}` : ""}
                {l.price_per_kg != null ? ` — ${l.price_per_kg} ${l.currency || ""}/kg` : ""}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
