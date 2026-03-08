"use client";

import { useState } from "react";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import { useDeals, useCalculateMargin } from "../hooks/useDeals";
import { MarginCalcRequest } from "../types";
import PieChart from "../charts/PieChart";

export default function DealsDashboard() {
  const [showCalculator, setShowCalculator] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [marginForm, setMarginForm] = useState<MarginCalcRequest>({
    purchase_price_per_kg: 4.5,
    purchase_currency: "USD",
    landed_costs_per_kg: 0.8,
    roast_and_pack_costs_per_kg: 1.2,
    yield_factor: 0.84,
    selling_price_per_kg: 12.0,
    selling_currency: "EUR",
    fx_usd_to_eur: null,
  });

  const { data: dealsData, isLoading, refetch } = useDeals({
    limit: 50,
    include_deleted: showArchived,
  });
  const calculateMargin = useCalculateMargin();
  const [busyId, setBusyId] = useState<number | null>(null);

  const deals = dealsData?.items || [];
  const activeDeals = deals.filter((d) => !(d as any).deleted_at);

  const stats = {
    total: activeDeals.length,
    totalValue: activeDeals.reduce((sum, d) => sum + ((d as any).value_eur || 0), 0),
    avgMargin: 15.5,
  };

  const handleCalculate = () => {
    calculateMargin.mutate(marginForm);
  };

  async function archiveLot(id: number) {
    if (!confirm("Deal archivieren?")) return;
    setBusyId(id);
    try {
      await apiFetch(`/deals/${id}`, { method: "DELETE" });
      await refetch();
    } catch (e) {
      console.error("Failed to archive deal:", e);
    } finally {
      setBusyId(null);
    }
  }

  async function restoreLot(id: number) {
    setBusyId(id);
    try {
      await apiFetch(`/deals/${id}/restore`, { method: "POST" });
      await refetch();
    } catch (e) {
      console.error("Failed to restore deal:", e);
    } finally {
      setBusyId(null);
    }
  }

  const costBreakdown = [
    { name: "Purchase", value: marginForm.purchase_price_per_kg },
    { name: "Landed Costs", value: marginForm.landed_costs_per_kg },
    { name: "Roast & Pack", value: marginForm.roast_and_pack_costs_per_kg },
  ];

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Deals & Margenrechner</div>
          <div className="muted">
            Verwalten Sie Deals, berechnen Sie Margen und analysieren Sie die Rentabilitaet
          </div>
        </div>
        <div className="actions">
          <label className="row" style={{ gap: 6 }}>
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            <span className="small muted">Archivierte anzeigen</span>
          </label>
          <button
            type="button"
            className="btn btnPrimary"
            onClick={() => setShowCalculator(!showCalculator)}
          >
            {showCalculator ? "Rechner verstecken" : "Margenrechner"}
          </button>
          <Link href="/lots" className="btn">
            Alle Lots anzeigen
          </Link>
        </div>
      </div>

      <div className="grid gridCols4" style={{ marginBottom: "18px" }}>
        <div className="panel card">
          <div className="cardLabel">Deals gesamt</div>
          <div className="cardValue">{stats.total}</div>
          <div className="cardHint">Aktiv und abgeschlossen</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Pipeline-Wert</div>
          <div className="cardValue">EUR {stats.totalValue.toLocaleString()}</div>
          <div className="cardHint">Gesamter Deal-Wert</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Durchschn. Marge</div>
          <div className="cardValue">{stats.avgMargin.toFixed(1)}%</div>
          <div className="cardHint">Durchschnittliche Bruttomarge</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Aktive Deals</div>
          <div className="cardValue">{activeDeals.filter((d) => (d as any).status !== "closed").length}</div>
          <div className="cardHint">In Bearbeitung</div>
        </div>
      </div>

      {showCalculator && (
        <div className="panel" style={{ padding: "18px", marginBottom: "18px" }}>
          <div className="h2">Echtzeit-Margenrechner</div>
          <div className="muted" style={{ marginBottom: "14px" }}>
            Berechnen Sie Rentabilitaetsszenarien fuer Kaffee-Deals
          </div>

          <div className="grid gridCols2" style={{ gap: "18px" }}>
            <div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                    Einkaufspreis pro kg (USD)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="input"
                    value={marginForm.purchase_price_per_kg}
                    onChange={(e) =>
                      setMarginForm({
                        ...marginForm,
                        purchase_price_per_kg: Number(e.target.value),
                      })
                    }
                  />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                    Landungskosten pro kg (EUR)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="input"
                    value={marginForm.landed_costs_per_kg}
                    onChange={(e) =>
                      setMarginForm({
                        ...marginForm,
                        landed_costs_per_kg: Number(e.target.value),
                      })
                    }
                  />
                  <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "4px" }}>
                    Inkl. Fracht, Versicherung, Zoll, Handling
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                    Roest- & Verpackungskosten pro kg (EUR)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="input"
                    value={marginForm.roast_and_pack_costs_per_kg}
                    onChange={(e) =>
                      setMarginForm({
                        ...marginForm,
                        roast_and_pack_costs_per_kg: Number(e.target.value),
                      })
                    }
                  />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                    Ertragsfaktor (Gruen zu Geroestet)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    className="input"
                    value={marginForm.yield_factor}
                    onChange={(e) =>
                      setMarginForm({ ...marginForm, yield_factor: Number(e.target.value) })
                    }
                  />
                  <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "4px" }}>
                    0.84 = 16% Gewichtsverlust beim Roesten
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                    Verkaufspreis pro kg (EUR)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="input"
                    value={marginForm.selling_price_per_kg}
                    onChange={(e) =>
                      setMarginForm({
                        ...marginForm,
                        selling_price_per_kg: Number(e.target.value),
                      })
                    }
                  />
                </div>
                <button
                  type="button"
                  className="btn btnPrimary"
                  onClick={handleCalculate}
                  disabled={calculateMargin.isPending}
                  style={{ marginTop: "10px" }}
                >
                  {calculateMargin.isPending ? "Berechne..." : "Marge berechnen"}
                </button>
              </div>
            </div>

            <div>
              {calculateMargin.isSuccess && calculateMargin.data ? (
                <div>
                  <div
                    className="panel"
                    style={{
                      padding: "18px",
                      background: "rgba(64,214,123,0.08)",
                      border: "1px solid rgba(64,214,123,0.25)",
                      marginBottom: "14px",
                    }}
                  >
                    <div style={{ fontWeight: "700", marginBottom: "12px" }}>Margenergebnisse</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {Object.entries(calculateMargin.data.outputs).map(([key, value]) => (
                        <div key={key} style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ fontSize: "13px", color: "var(--muted)" }}>
                            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                          </span>
                          <span style={{ fontWeight: "700" }}>
                            {typeof value === "number" ? value.toFixed(2) : value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <PieChart data={costBreakdown} dataKey="value" nameKey="name" title="Kostenaufschluesselung" />
                </div>
              ) : (
                <div
                  style={{
                    padding: "40px",
                    textAlign: "center",
                    color: "var(--muted)",
                    border: "1px dashed var(--border)",
                    borderRadius: "12px",
                  }}
                >
                  Geben Sie Werte ein und klicken Sie auf
                  &quot;Marge berechnen&quot;, um Ergebnisse zu sehen
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="panel" style={{ padding: "18px" }}>
        <div className="h2">Aktive Deals</div>
        <div className="muted" style={{ marginBottom: "14px" }}>
          {isLoading ? "Lade Deals..." : `${deals.length} Deals im System`}
        </div>

        {deals.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Referenz</th>
                  <th>Herkunft</th>
                  <th>Sorte</th>
                  <th>Prozess</th>
                  <th>Qualitaet</th>
                  <th>Gewicht (kg)</th>
                  <th>Cupping-Score</th>
                  <th>Status</th>
                  <th>Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {deals.map((lot) => (
                  <tr key={lot.id}>
                    <td style={{ fontWeight: "600" }}>{(lot as any).reference || `LOT-${lot.id}`}</td>
                    <td>{(lot as any).origin || "-"}</td>
                    <td>{(lot as any).variety || "-"}</td>
                    <td>{(lot as any).process || "-"}</td>
                    <td>{(lot as any).grade || "-"}</td>
                    <td>{(lot as any).weight_kg?.toLocaleString() || "-"}</td>
                    <td>
                      {(lot as any).cupping_score ? (
                        <span className="badge badgeOk">{(lot as any).cupping_score}</span>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>
                      {(lot as any).deleted_at ? (
                        <span className="badge badgeWarn">archiviert</span>
                      ) : (
                        <span className="badge">{(lot as any).status || "active"}</span>
                      )}
                    </td>
                    <td>
                      <Link href={`/lots/${lot.id}`} className="link">
                        Ansehen -
                      </Link>
                      {(lot as any).deleted_at ? (
                        <button
                          className="btn"
                          style={{ marginLeft: 8 }}
                          onClick={() => restoreLot(lot.id)}
                          disabled={busyId === lot.id}
                        >
                          Restore
                        </button>
                      ) : (
                        <button
                          className="btn"
                          style={{ marginLeft: 8 }}
                          onClick={() => archiveLot(lot.id)}
                          disabled={busyId === lot.id}
                        >
                          Archivieren
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty" style={{ padding: "40px", textAlign: "center", color: "var(--muted)" }}>
            Keine Deals gefunden. Erstellen Sie einen Deal, um Margen zu verfolgen.
          </div>
        )}
      </div>
    </div>
  );
}
