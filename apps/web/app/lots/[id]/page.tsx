"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "../../../lib/api";

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
  notes?: string | null;
};

type MarginRun = {
  id: number;
  lot_id: number;
  profile: string;
  computed_at: string;
  inputs: any;
  outputs: any;
};

export default function LotDetailPage() {
  const params = useParams();
  const id = useMemo(() => String(params?.id || ""), [params]);
  const [lot, setLot] = useState<Lot | null>(null);
  const [runs, setRuns] = useState<MarginRun[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [profile, setProfile] = useState("conservative");
  const [calc, setCalc] = useState<any>({
    purchase_price_per_kg: "",
    purchase_currency: "USD",
    landed_costs_per_kg: "0.0",
    roast_and_pack_costs_per_kg: "0.0",
    yield_factor: "0.84",
    selling_price_per_kg: "",
    selling_currency: "EUR",
    fx_usd_to_eur: "",
  });

  async function loadAll() {
    setErr(null);
    try {
      const l = await apiFetch<Lot>(`/lots/${id}`);
      setLot(l);
      // Prime calc form from lot if present
      setCalc((prev: any) => ({
        ...prev,
        purchase_price_per_kg: l.price_per_kg ?? prev.purchase_price_per_kg,
        purchase_currency: l.currency || prev.purchase_currency,
      }));
      const r = await apiFetch<MarginRun[]>(`/margins/lots/${id}/runs?limit=50`);
      setRuns(r);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    if (!id) return;
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function computeAndStore() {
    setBusy(true);
    setErr(null);
    try {
      const payload: any = {
        purchase_price_per_kg: Number(calc.purchase_price_per_kg),
        purchase_currency: String(calc.purchase_currency || "USD"),
        landed_costs_per_kg: Number(calc.landed_costs_per_kg || 0),
        roast_and_pack_costs_per_kg: Number(calc.roast_and_pack_costs_per_kg || 0),
        yield_factor: Number(calc.yield_factor || 0.84),
        selling_price_per_kg: Number(calc.selling_price_per_kg),
        selling_currency: String(calc.selling_currency || "EUR"),
      };
      if (calc.fx_usd_to_eur) payload.fx_usd_to_eur = Number(calc.fx_usd_to_eur);

      await apiFetch<MarginRun>(`/margins/lots/${id}/runs?profile=${encodeURIComponent(profile)}`,
        { method: "POST", body: JSON.stringify(payload) }
      );
      const r = await apiFetch<MarginRun[]>(`/margins/lots/${id}/runs?limit=50`);
      setRuns(r);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1>Lot</h1>
      {err && <div style={{ color: "crimson" }}>{err}</div>}

      {lot ? (
        <>
          <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 12, marginBottom: 16 }}>
            <div><b>{lot.name}</b></div>
            <div style={{ fontSize: 12, color: "#555" }}>
              ID {lot.id} — Coop #{lot.cooperative_id}
              {lot.crop_year ? ` — Crop ${lot.crop_year}` : ""}
              {lot.incoterm ? ` — ${lot.incoterm}` : ""}
            </div>
            <div style={{ marginTop: 8 }}>
              <div><b>Preis:</b> {lot.price_per_kg ?? "-"} {lot.currency ?? ""} / kg (green)</div>
              <div><b>Gewicht:</b> {lot.weight_kg ?? "-"} kg</div>
              <div><b>Expected SCA:</b> {lot.expected_cupping_score ?? "-"}</div>
            </div>
          </div>

          <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 12, marginBottom: 16 }}>
            <b>Margenrechnung speichern</b>
            <div style={{ marginTop: 10, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10 }}>
              <input placeholder="purchase_price_per_kg" value={calc.purchase_price_per_kg} onChange={(e) => setCalc({ ...calc, purchase_price_per_kg: e.target.value })} />
              <input placeholder="purchase_currency" value={calc.purchase_currency} onChange={(e) => setCalc({ ...calc, purchase_currency: e.target.value })} />
              <input placeholder="landed_costs_per_kg" value={calc.landed_costs_per_kg} onChange={(e) => setCalc({ ...calc, landed_costs_per_kg: e.target.value })} />
              <input placeholder="roast_and_pack_costs_per_kg" value={calc.roast_and_pack_costs_per_kg} onChange={(e) => setCalc({ ...calc, roast_and_pack_costs_per_kg: e.target.value })} />
              <input placeholder="yield_factor" value={calc.yield_factor} onChange={(e) => setCalc({ ...calc, yield_factor: e.target.value })} />
              <input placeholder="selling_price_per_kg" value={calc.selling_price_per_kg} onChange={(e) => setCalc({ ...calc, selling_price_per_kg: e.target.value })} />
              <input placeholder="selling_currency" value={calc.selling_currency} onChange={(e) => setCalc({ ...calc, selling_currency: e.target.value })} />
              <input placeholder="fx_usd_to_eur (optional)" value={calc.fx_usd_to_eur} onChange={(e) => setCalc({ ...calc, fx_usd_to_eur: e.target.value })} />
              <input placeholder="profile (conservative/...)" value={profile} onChange={(e) => setProfile(e.target.value)} />
            </div>
            <button
              onClick={computeAndStore}
              disabled={busy}
              style={{ marginTop: 10, padding: "8px 12px", borderRadius: 8, border: "1px solid #eee", background: "white", cursor: "pointer" }}
            >
              {busy ? "Rechnen…" : "Berechnen & speichern"}
            </button>
            <div style={{ fontSize: 12, color: "#555", marginTop: 6 }}>
              Ergebnis wird als <i>Margin Run</i> in der DB gespeichert.
            </div>
          </div>

          <h2>Margin Runs</h2>
          {runs.length === 0 ? (
            <div>Keine Runs vorhanden.</div>
          ) : (
            <ul>
              {runs.map((r) => (
                <li key={r.id} style={{ marginBottom: 10 }}>
                  <div>
                    <b>Run #{r.id}</b> — {r.profile} — {new Date(r.computed_at).toLocaleString()}
                  </div>
                  <div style={{ fontSize: 12, color: "#555" }}>
                    GM/kg: {r.outputs?.gross_margin_per_kg?.toFixed?.(2) ?? r.outputs?.gross_margin_per_kg ?? "-"} — GM%: {r.outputs?.gross_margin_pct?.toFixed?.(1) ?? r.outputs?.gross_margin_pct ?? "-"}
                  </div>
                  <details>
                    <summary style={{ cursor: "pointer" }}>Details</summary>
                    <pre style={{ marginTop: 6, padding: 10, background: "#fafafa", border: "1px solid #eee", borderRadius: 12, overflowX: "auto" }}>
{JSON.stringify({ inputs: r.inputs, outputs: r.outputs }, null, 2)}
                    </pre>
                  </details>
                </li>
              ))}
            </ul>
          )}
        </>
      ) : (
        <div>Loading…</div>
      )}
    </div>
  );
}
