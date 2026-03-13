"use client";

import { useState } from "react";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import { useDeals, useCalculateMargin } from "../hooks/useDeals";
import { Deal, MarginCalcRequest } from "../types";
import PieChart from "../charts/PieChart";

/* ============================================================
   DEALS & MARGIN CALCULATOR - ENTERPRISE VIEW
   ============================================================ */

function readMetaString(meta: Deal["meta"], key: string): string | null {
  if (!meta) return null;
  const value = meta[key];
  return typeof value === "string" ? value : null;
}

function formatOutputValue(value: unknown): string {
  if (typeof value === "number") return value.toFixed(2);
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return value ? "Ja" : "Nein";
  return "-";
}

function formatOutputLabel(key: string): string {
  const labels: Record<string, string> = {
    gross_margin_pct: "Bruttomarge %",
    gross_margin_eur: "Bruttomarge EUR",
    cost_per_kg_roasted: "Kosten/kg geroestet",
    profit_per_kg: "Gewinn/kg",
    break_even_price: "Break-Even Preis",
  };
  return labels[key] || key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

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
  const activeDeals = deals.filter((d) => !d.deleted_at);

  const stats = {
    total: activeDeals.length,
    totalValue: activeDeals.reduce((sum, d) => sum + (d.value_eur || 0), 0),
    avgMargin: 15.5,
    inProgress: activeDeals.filter((d) => d.status !== "closed").length,
  };

  const handleCalculate = () => {
    calculateMargin.mutate(marginForm);
  };

  async function archiveDeal(id: number) {
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

  async function restoreDeal(id: number) {
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
    { name: "Einkauf", value: marginForm.purchase_price_per_kg },
    { name: "Landung", value: marginForm.landed_costs_per_kg },
    { name: "Verarbeitung", value: marginForm.roast_and_pack_costs_per_kg },
  ];

  return (
    <div className="page">
      <div className="content">
        {/* Page Header */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Deals & Margenrechner</h1>
            <p className="subtitle">
              Deals verwalten, Margen berechnen und Rentabilitaet analysieren
            </p>
          </div>
          <div className="pageHeaderActions">
            <label className="checkboxLabel">
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
              />
              Archivierte anzeigen
            </label>
            <button
              type="button"
              className={`btn ${showCalculator ? "" : "btnPrimary"}`}
              onClick={() => setShowCalculator(!showCalculator)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="4" y="2" width="16" height="20" rx="2"/>
                <line x1="8" y1="6" x2="16" y2="6"/>
                <line x1="16" y1="14" x2="16" y2="18"/>
                <line x1="16" y1="10" x2="16" y2="10.01"/>
                <line x1="12" y1="18" x2="12" y2="18.01"/>
                <line x1="8" y1="18" x2="8" y2="18.01"/>
                <line x1="12" y1="14" x2="12" y2="14.01"/>
                <line x1="8" y1="14" x2="8" y2="14.01"/>
                <line x1="12" y1="10" x2="12" y2="10.01"/>
                <line x1="8" y1="10" x2="8" y2="10.01"/>
              </svg>
              {showCalculator ? "Rechner schliessen" : "Margenrechner"}
            </button>
            <Link href="/lots" className="btn">
              Alle Lots
            </Link>
          </div>
        </header>

        {/* KPI Grid */}
        <div className="kpiGrid">
          <div className="kpiCard">
            <span className="cardLabel">Deals Gesamt</span>
            <span className="cardValue">{stats.total}</span>
            <span className="cardHint">Aktive Deals</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Pipeline-Wert</span>
            <span className="cardValue">
              {stats.totalValue > 0 
                ? `${(stats.totalValue / 1000).toFixed(0)}k` 
                : "0"}
            </span>
            <span className="cardHint">EUR Gesamtwert</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Durchschn. Marge</span>
            <span className="cardValue">{stats.avgMargin.toFixed(1)}%</span>
            <span className="cardHint">Bruttomarge</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">In Bearbeitung</span>
            <span className="cardValue">{stats.inProgress}</span>
            <span className="cardHint">Offene Deals</span>
          </div>
        </div>

        {/* Margin Calculator */}
        {showCalculator && (
          <div className="panel" style={{ marginBottom: "var(--space-6)" }}>
            <div className="panelHeader">
              <h2 className="panelTitle">Echtzeit-Margenrechner</h2>
              <span className="badge badgeInfo">Kalkulator</span>
            </div>
            <div className="panelBody">
              <p className="subtitle" style={{ marginBottom: "var(--space-5)" }}>
                Berechnen Sie Rentabilitaetsszenarien fuer Kaffee-Deals
              </p>

              <div className="grid2col">
                {/* Input Fields */}
                <div className="fieldStack">
                  <div className="fieldGrid2">
                    <div className="field">
                      <label className="fieldLabel">Einkaufspreis/kg (USD)</label>
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
                    <div className="field">
                      <label className="fieldLabel">Verkaufspreis/kg (EUR)</label>
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
                  </div>
                  
                  <div className="field">
                    <label className="fieldLabel">Landungskosten/kg (EUR)</label>
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
                    <span className="fieldHint">Fracht, Versicherung, Zoll, Handling</span>
                  </div>
                  
                  <div className="field">
                    <label className="fieldLabel">Roest- & Verpackungskosten/kg (EUR)</label>
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
                  
                  <div className="field">
                    <label className="fieldLabel">Ertragsfaktor</label>
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
                    <span className="fieldHint">0.84 = 16% Gewichtsverlust beim Roesten</span>
                  </div>

                  <div className="btnGroup">
                    <button
                      type="button"
                      className="btn btnPrimary"
                      onClick={handleCalculate}
                      disabled={calculateMargin.isPending}
                    >
                      {calculateMargin.isPending ? "Berechne..." : "Marge berechnen"}
                    </button>
                  </div>
                </div>

                {/* Results */}
                <div>
                  {calculateMargin.isSuccess && calculateMargin.data ? (
                    <div>
                      <div className="card" style={{ 
                        background: "var(--color-success-subtle)", 
                        borderColor: "var(--color-success-border)",
                        marginBottom: "var(--space-4)"
                      }}>
                        <h3 className="h4" style={{ marginBottom: "var(--space-4)" }}>
                          Margenergebnisse
                        </h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                          {Object.entries(calculateMargin.data.outputs).map(([key, value]) => (
                            <div key={key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <span className="small muted">{formatOutputLabel(key)}</span>
                              <span style={{ fontWeight: 600, fontFamily: "var(--font-mono)" }}>
                                {formatOutputValue(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <PieChart data={costBreakdown} dataKey="value" nameKey="name" title="Kostenaufschluesselung" />
                    </div>
                  ) : (
                    <div className="emptyState" style={{ 
                      height: "100%", 
                      minHeight: "200px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexDirection: "column"
                    }}>
                      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.3, marginBottom: "var(--space-3)" }}>
                        <rect x="4" y="2" width="16" height="20" rx="2"/>
                        <line x1="8" y1="6" x2="16" y2="6"/>
                        <line x1="8" y1="10" x2="16" y2="10"/>
                        <line x1="8" y1="14" x2="16" y2="14"/>
                        <line x1="8" y1="18" x2="12" y2="18"/>
                      </svg>
                      <p className="small muted">
                        Werte eingeben und berechnen
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Deals Table */}
        <div className="panel">
          <div className="panelHeader">
            <h2 className="panelTitle">Aktive Deals</h2>
            <span className="badge">
              {isLoading ? "..." : `${deals.length} Eintraege`}
            </span>
          </div>

          {deals.length > 0 ? (
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Referenz</th>
                    <th>Herkunft</th>
                    <th>Sorte</th>
                    <th>Prozess</th>
                    <th>Qualitaet</th>
                    <th>Gewicht</th>
                    <th>Cupping</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {deals.map((deal) => (
                    <tr key={deal.id}>
                      <td>
                        <span style={{ fontWeight: 600, fontFamily: "var(--font-mono)", fontSize: "var(--font-size-sm)" }}>
                          {readMetaString(deal.meta, "reference") || `LOT-${deal.id}`}
                        </span>
                      </td>
                      <td>{deal.origin_region || deal.origin_country || "-"}</td>
                      <td>{deal.variety || "-"}</td>
                      <td>{deal.process_method || "-"}</td>
                      <td>{deal.quality_grade || "-"}</td>
                      <td>
                        {deal.weight_kg 
                          ? `${(deal.weight_kg / 1000).toFixed(1)}t` 
                          : "-"}
                      </td>
                      <td>
                        {deal.cupping_score ? (
                          <span className="badge badgeOk">{deal.cupping_score}</span>
                        ) : (
                          <span className="badge">-</span>
                        )}
                      </td>
                      <td>
                        {deal.deleted_at ? (
                          <span className="badge badgeWarn">Archiviert</span>
                        ) : (
                          <span className="badge">{deal.status || "Aktiv"}</span>
                        )}
                      </td>
                      <td>
                        <div className="tableActions">
                          <Link href={`/lots/${deal.id}`} className="btn btnSm btnGhost">
                            Details
                          </Link>
                          {deal.deleted_at ? (
                            <button
                              className="btn btnSm"
                              onClick={() => restoreDeal(deal.id)}
                              disabled={busyId === deal.id}
                            >
                              Wiederherstellen
                            </button>
                          ) : (
                            <button
                              className="btn btnSm btnDanger"
                              onClick={() => archiveDeal(deal.id)}
                              disabled={busyId === deal.id}
                            >
                              Archivieren
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="panelBody">
              <div className="emptyState">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.3, marginBottom: "var(--space-4)" }}>
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
                <h3 className="h4">Keine Deals gefunden</h3>
                <p className="subtitle">
                  Erstellen Sie einen Deal, um Margen zu verfolgen und Rentabilitaet zu analysieren.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
