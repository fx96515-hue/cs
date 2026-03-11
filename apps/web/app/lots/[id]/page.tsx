"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import { JsonObject } from "../../types";
import { toErrorMessage } from "../../utils/error";

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
  deleted_at?: string | null;
};

type MarginRun = {
  id: number;
  lot_id: number;
  profile: string;
  computed_at: string;
  inputs: JsonObject;
  outputs: JsonObject;
};

type CalcState = {
  purchase_price_per_kg: string;
  purchase_currency: string;
  landed_costs_per_kg: string;
  roast_and_pack_costs_per_kg: string;
  yield_factor: string;
  selling_price_per_kg: string;
  selling_currency: string;
  fx_usd_to_eur: string;
};

type MarginRunPayload = {
  purchase_price_per_kg: number;
  purchase_currency: string;
  landed_costs_per_kg: number;
  roast_and_pack_costs_per_kg: number;
  yield_factor: number;
  selling_price_per_kg: number;
  selling_currency: string;
  fx_usd_to_eur?: number;
};

const INITIAL_CALC: CalcState = {
  purchase_price_per_kg: "",
  purchase_currency: "USD",
  landed_costs_per_kg: "0.0",
  roast_and_pack_costs_per_kg: "0.0",
  yield_factor: "0.84",
  selling_price_per_kg: "",
  selling_currency: "EUR",
  fx_usd_to_eur: "",
};

export default function LotDetailPage() {
  const params = useParams();
  const id = useMemo(() => String(params?.id || ""), [params]);
  const router = useRouter();
  const [lot, setLot] = useState<Lot | null>(null);
  const [runs, setRuns] = useState<MarginRun[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [profile, setProfile] = useState("conservative");
  const [calc, setCalc] = useState<CalcState>(INITIAL_CALC);

  const loadAll = useCallback(async () => {
    setErr(null);
    try {
      const l = await apiFetch<Lot>(`/lots/${id}?include_deleted=true`);
      setLot(l);
      setCalc((prev) => ({
        ...prev,
        purchase_price_per_kg:
          l.price_per_kg !== null && l.price_per_kg !== undefined
            ? String(l.price_per_kg)
            : prev.purchase_price_per_kg,
        purchase_currency: l.currency || prev.purchase_currency,
      }));
      const r = await apiFetch<MarginRun[]>(`/margins/lots/${id}/runs?limit=50`);
      setRuns(r);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;
    loadAll();
  }, [id, loadAll]);

  async function computeAndStore() {
    setBusy(true);
    setErr(null);
    try {
      const payload: MarginRunPayload = {
        purchase_price_per_kg: Number(calc.purchase_price_per_kg),
        purchase_currency: String(calc.purchase_currency || "USD"),
        landed_costs_per_kg: Number(calc.landed_costs_per_kg || 0),
        roast_and_pack_costs_per_kg: Number(calc.roast_and_pack_costs_per_kg || 0),
        yield_factor: Number(calc.yield_factor || 0.84),
        selling_price_per_kg: Number(calc.selling_price_per_kg),
        selling_currency: String(calc.selling_currency || "EUR"),
      };
      if (calc.fx_usd_to_eur) payload.fx_usd_to_eur = Number(calc.fx_usd_to_eur);

      await apiFetch<MarginRun>(
        `/margins/lots/${id}/runs?profile=${encodeURIComponent(profile)}`,
        { method: "POST", body: JSON.stringify(payload) },
      );
      const r = await apiFetch<MarginRun[]>(`/margins/lots/${id}/runs?limit=50`);
      setRuns(r);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function archive() {
    setErr(null);
    if (!confirm("Lot archivieren?")) return;
    try {
      await apiFetch(`/lots/${id}`, { method: "DELETE" });
      const l = await apiFetch<Lot>(`/lots/${id}?include_deleted=true`);
      setLot(l);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    }
  }

  async function restore() {
    setErr(null);
    try {
      const l = await apiFetch<Lot>(`/lots/${id}/restore`, { method: "POST" });
      setLot(l);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    }
  }

  return (
    <div>
      <h1>Lot</h1>
      <div style={{ marginBottom: 10 }}>
        {lot?.deleted_at ? (
          <button onClick={restore} style={{ marginRight: 8 }}>
            Wiederherstellen
          </button>
        ) : (
          <button onClick={archive} style={{ marginRight: 8 }}>
            Archivieren
          </button>
        )}
        <button onClick={() => router.push("/lots")}>Zur Liste</button>
      </div>
      {err && <div style={{ color: "crimson" }}>{err}</div>}

      {lot ? (
        <>
          {lot.deleted_at ? (
            <div
              style={{
                padding: 10,
                background: "#fff3cd",
                border: "1px solid #ffeeba",
                borderRadius: 8,
                marginBottom: 12,
              }}
            >
              Dieses Lot ist archiviert.
            </div>
          ) : null}
          <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 12, marginBottom: 16 }}>
            <div>
              <b>{lot.name}</b>
            </div>
            <div style={{ fontSize: 12, color: "#555" }}>
              ID {lot.id} - Coop #{lot.cooperative_id}
              {lot.crop_year ? ` - Crop ${lot.crop_year}` : ""}
              {lot.incoterm ? ` - ${lot.incoterm}` : ""}
            </div>
            <div style={{ marginTop: 8 }}>
              <div>
                <b>Preis:</b> {lot.price_per_kg ?? "-"} {lot.currency ?? ""} / kg (green)
              </div>
              <div>
                <b>Gewicht:</b> {lot.weight_kg ?? "-"} kg
              </div>
              <div>
                <b>Expected SCA:</b> {lot.expected_cupping_score ?? "-"}
              </div>
            </div>
          </div>

          <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 12, marginBottom: 16 }}>
            <b>Margenrechnung speichern</b>
            <div
              style={{
                marginTop: 10,
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: 10,
              }}
            >
              <input
                placeholder="purchase_price_per_kg"
                value={calc.purchase_price_per_kg}
                onChange={(e) => setCalc({ ...calc, purchase_price_per_kg: e.target.value })}
              />
              <input
                placeholder="purchase_currency"
                value={calc.purchase_currency}
                onChange={(e) => setCalc({ ...calc, purchase_currency: e.target.value })}
              />
              <input
                placeholder="landed_costs_per_kg"
                value={calc.landed_costs_per_kg}
                onChange={(e) => setCalc({ ...calc, landed_costs_per_kg: e.target.value })}
              />
              <input
                placeholder="roast_and_pack_costs_per_kg"
                value={calc.roast_and_pack_costs_per_kg}
                onChange={(e) => setCalc({ ...calc, roast_and_pack_costs_per_kg: e.target.value })}
              />
              <input
                placeholder="yield_factor"
                value={calc.yield_factor}
                onChange={(e) => setCalc({ ...calc, yield_factor: e.target.value })}
              />
              <input
                placeholder="selling_price_per_kg"
                value={calc.selling_price_per_kg}
                onChange={(e) => setCalc({ ...calc, selling_price_per_kg: e.target.value })}
              />
              <input
                placeholder="selling_currency"
                value={calc.selling_currency}
                onChange={(e) => setCalc({ ...calc, selling_currency: e.target.value })}
              />
              <input
                placeholder="fx_usd_to_eur (optional)"
                value={calc.fx_usd_to_eur}
                onChange={(e) => setCalc({ ...calc, fx_usd_to_eur: e.target.value })}
              />
              <input
                placeholder="profile (conservative/...)"
                value={profile}
                onChange={(e) => setProfile(e.target.value)}
              />
            </div>
            <button
              onClick={computeAndStore}
              disabled={busy}
              style={{
                marginTop: 10,
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid #eee",
                background: "white",
                cursor: "pointer",
              }}
            >
              {busy ? "Rechnen..." : "Berechnen & speichern"}
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
              {runs.map((r) => {
                const grossMarginPerKg = r.outputs.gross_margin_per_kg;
                const gmKg =
                  typeof grossMarginPerKg === "number"
                    ? grossMarginPerKg.toFixed(2)
                    : typeof grossMarginPerKg === "string"
                      ? grossMarginPerKg
                      : "-";
                const grossMarginPct = r.outputs.gross_margin_pct;
                const gmPct =
                  typeof grossMarginPct === "number"
                    ? grossMarginPct.toFixed(1)
                    : typeof grossMarginPct === "string"
                      ? grossMarginPct
                      : "-";
                return (
                  <li key={r.id} style={{ marginBottom: 10 }}>
                    <div>
                      <b>Run #{r.id}</b> - {r.profile} - {new Date(r.computed_at).toLocaleString()}
                    </div>
                    <div style={{ fontSize: 12, color: "#555" }}>
                      GM/kg: {gmKg} - GM%: {gmPct}
                    </div>
                    <details>
                      <summary style={{ cursor: "pointer" }}>Details</summary>
                      <pre
                        style={{
                          marginTop: 6,
                          padding: 10,
                          background: "#fafafa",
                          border: "1px solid #eee",
                          borderRadius: 12,
                          overflowX: "auto",
                        }}
                      >
{JSON.stringify({ inputs: r.inputs, outputs: r.outputs }, null, 2)}
                      </pre>
                    </details>
                  </li>
                );
              })}
            </ul>
          )}
        </>
      ) : (
        <div>Loading...</div>
      )}
    </div>
  );
}
