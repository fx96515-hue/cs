"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import { ErrorPanel } from "../../components/AlertError";
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

function formatOutputValue(value: unknown, precision: number): string {
  if (typeof value === "number") return value.toFixed(precision);
  if (typeof value === "string") return value;
  return "-";
}

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
    <div className="content">
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Lot-Details</h1>
          <p className="subtitle">Stammdaten, Margenberechnung und gespeicherte Runs.</p>
        </div>
        <div className="pageHeaderActions">
          {lot?.deleted_at ? (
            <button className="btn" onClick={restore}>
              Wiederherstellen
            </button>
          ) : (
            <button className="btn btnDanger" onClick={archive}>
              Archivieren
            </button>
          )}
          <button className="btn" onClick={() => router.push("/lots")}>
            Zur Liste
          </button>
        </div>
      </header>

      {err ? <ErrorPanel message={err} onRetry={loadAll} /> : null}

      {!lot ? (
        <section className="panel">
          <div className="panelBody">
            <div className="muted">Laedt Lot-Daten...</div>
          </div>
        </section>
      ) : (
        <>
          {lot.deleted_at ? (
            <div className="alert warn">
              <div className="alertText">Dieses Lot ist archiviert.</div>
            </div>
          ) : null}

          <section className="panel">
            <div className="panelHeader">
              <div className="panelTitle">{lot.name}</div>
            </div>
            <div className="panelBody">
              <div className="muted">
                ID {lot.id} - Coop #{lot.cooperative_id}
                {lot.crop_year ? ` - Crop ${lot.crop_year}` : ""}
                {lot.incoterm ? ` - ${lot.incoterm}` : ""}
              </div>
              <div className="row" style={{ marginTop: 12, flexWrap: "wrap" }}>
                <span><b>Preis:</b> {lot.price_per_kg ?? "-"} {lot.currency ?? ""} / kg (green)</span>
                <span><b>Gewicht:</b> {lot.weight_kg ?? "-"} kg</span>
                <span><b>Expected SCA:</b> {lot.expected_cupping_score ?? "-"}</span>
              </div>
            </div>
          </section>

          <section className="panel" style={{ marginTop: "var(--space-4)" }}>
            <div className="panelHeader">
              <div className="panelTitle">Margenrechnung speichern</div>
            </div>
            <div className="panelBody">
              <div
                style={{
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
              <div className="row" style={{ marginTop: 10 }}>
                <button className="btn" onClick={computeAndStore} disabled={busy}>
                  {busy ? "Rechnen..." : "Berechnen & speichern"}
                </button>
                <span className="muted">Ergebnis wird als Margin Run in der DB gespeichert.</span>
              </div>
            </div>
          </section>

          <section className="panel" style={{ marginTop: "var(--space-4)" }}>
            <div className="panelHeader">
              <div className="panelTitle">Margin Runs</div>
            </div>
            <div className="panelBody">
              {runs.length === 0 ? (
                <div className="muted">Keine Runs vorhanden.</div>
              ) : (
                <div className="list">
                  {runs.map((r) => {
                    const gmKg = formatOutputValue(r.outputs.gross_margin_per_kg, 2);
                    const gmPct = formatOutputValue(r.outputs.gross_margin_pct, 1);
                    return (
                      <div key={r.id} className="listItem" style={{ display: "block" }}>
                        <div className="rowBetween" style={{ alignItems: "flex-start" }}>
                          <div>
                            <div className="listTitle">
                              Run #{r.id} - {r.profile}
                            </div>
                            <div className="listMeta">
                              <span>{new Date(r.computed_at).toLocaleString()}</span>
                              <span className="dot">-</span>
                              <span>GM/kg: {gmKg}</span>
                              <span className="dot">-</span>
                              <span>GM%: {gmPct}</span>
                            </div>
                          </div>
                        </div>
                        <details style={{ marginTop: 8 }}>
                          <summary style={{ cursor: "pointer" }}>Details</summary>
                          <pre className="codeBox" style={{ marginTop: 6, overflowX: "auto" }}>
{JSON.stringify({ inputs: r.inputs, outputs: r.outputs }, null, 2)}
                          </pre>
                        </details>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
