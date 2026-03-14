"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import { toErrorMessage } from "../utils/error";

type FeatureCategory = {
  name: string;
  features: Feature[];
};

type Feature = {
  name: string;
  description: string;
  type: "numeric" | "categorical" | "boolean";
  importance: number;
  coverage: number;
  lastComputed: string;
};

type QualityReport = {
  totalFeatures: number;
  avgCoverage: number;
  avgImportance: number;
  missingDataPoints: number;
  lastUpdate: string;
};

// Demo data
const DEMO_CATEGORIES: FeatureCategory[] = [
  {
    name: "Fracht-Features (15)",
    features: [
      { name: "fuel_price_index", description: "Treibstoffpreis-Index", type: "numeric", importance: 0.92, coverage: 98.5, lastComputed: "2026-03-14 08:00" },
      { name: "port_congestion_score", description: "Hafen-Auslastung", type: "numeric", importance: 0.88, coverage: 95.2, lastComputed: "2026-03-14 08:00" },
      { name: "seasonal_demand_index", description: "Saisonale Nachfrage", type: "numeric", importance: 0.85, coverage: 100, lastComputed: "2026-03-14 08:00" },
      { name: "carrier_reliability_score", description: "Spediteur-Zuverlaessigkeit", type: "numeric", importance: 0.82, coverage: 89.3, lastComputed: "2026-03-14 08:00" },
      { name: "route_complexity", description: "Routen-Komplexitaet", type: "numeric", importance: 0.78, coverage: 100, lastComputed: "2026-03-14 08:00" },
      { name: "container_availability", description: "Container-Verfuegbarkeit", type: "numeric", importance: 0.75, coverage: 92.1, lastComputed: "2026-03-14 08:00" },
      { name: "exchange_rate_volatility", description: "Wechselkurs-Volatilitaet", type: "numeric", importance: 0.73, coverage: 100, lastComputed: "2026-03-14 08:00" },
      { name: "weather_delay_probability", description: "Wetter-Verzoegerungs-Wahrsch.", type: "numeric", importance: 0.71, coverage: 87.6, lastComputed: "2026-03-14 08:00" },
    ],
  },
  {
    name: "Preis-Features (20)",
    features: [
      { name: "market_sentiment_score", description: "Markt-Sentiment", type: "numeric", importance: 0.94, coverage: 96.8, lastComputed: "2026-03-14 08:00" },
      { name: "ice_futures_correlation", description: "ICE Futures Korrelation", type: "numeric", importance: 0.91, coverage: 100, lastComputed: "2026-03-14 08:00" },
      { name: "global_coffee_stock_level", description: "Globale Lagerbestaende", type: "numeric", importance: 0.89, coverage: 94.5, lastComputed: "2026-03-14 08:00" },
      { name: "peru_production_forecast", description: "Peru Produktions-Prognose", type: "numeric", importance: 0.87, coverage: 91.2, lastComputed: "2026-03-14 08:00" },
      { name: "frost_risk_index", description: "Frost-Risiko Index", type: "numeric", importance: 0.85, coverage: 88.9, lastComputed: "2026-03-14 08:00" },
      { name: "drought_stress_index", description: "Duerrestress Index", type: "numeric", importance: 0.83, coverage: 85.4, lastComputed: "2026-03-14 08:00" },
      { name: "quality_cupping_trend", description: "Cupping-Score Trend", type: "numeric", importance: 0.80, coverage: 78.3, lastComputed: "2026-03-14 08:00" },
      { name: "certifications_premium", description: "Zertifizierungs-Premium", type: "numeric", importance: 0.77, coverage: 100, lastComputed: "2026-03-14 08:00" },
    ],
  },
  {
    name: "Cross-Features (15)",
    features: [
      { name: "freight_to_price_ratio", description: "Fracht-zu-Preis Verhaeltnis", type: "numeric", importance: 0.90, coverage: 95.6, lastComputed: "2026-03-14 08:00" },
      { name: "total_landed_cost_estimate", description: "Gesamtkosten-Schaetzung", type: "numeric", importance: 0.88, coverage: 93.2, lastComputed: "2026-03-14 08:00" },
      { name: "deal_profitability_forecast", description: "Profitabilitaets-Prognose", type: "numeric", importance: 0.86, coverage: 89.8, lastComputed: "2026-03-14 08:00" },
      { name: "temporal_seasonality", description: "Saisonalitaet", type: "numeric", importance: 0.82, coverage: 100, lastComputed: "2026-03-14 08:00" },
      { name: "region_reputation_score", description: "Regions-Reputation", type: "numeric", importance: 0.79, coverage: 100, lastComputed: "2026-03-14 08:00" },
      { name: "supply_disruption_risk", description: "Lieferketten-Risiko", type: "numeric", importance: 0.76, coverage: 87.5, lastComputed: "2026-03-14 08:00" },
    ],
  },
];

const DEMO_QUALITY: QualityReport = {
  totalFeatures: 50,
  avgCoverage: 93.2,
  avgImportance: 0.83,
  missingDataPoints: 1247,
  lastUpdate: "2026-03-14 08:00",
};

export default function FeaturesPage() {
  const [categories, setCategories] = useState<FeatureCategory[]>([]);
  const [quality, setQuality] = useState<QualityReport | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [busy, setBusy] = useState(false);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const push = useCallback((line: string) => {
    setLog((prev) => [`${new Date().toLocaleTimeString()}  ${line}`, ...prev].slice(0, 30));
  }, []);

  const loadData = useCallback(async () => {
    if (isDemoMode()) {
      setIsDemo(true);
      setCategories(DEMO_CATEGORIES);
      setQuality(DEMO_QUALITY);
      return;
    }
    setBusy(true);
    try {
      const [featuresRes, qualityRes] = await Promise.all([
        apiFetch<FeatureCategory[]>("/features/importance"),
        apiFetch<QualityReport>("/features/quality-report"),
      ]);
      setCategories(featuresRes);
      setQuality(qualityRes);
      push("Feature-Daten geladen");
    } catch (error: unknown) {
      push(`Fehler: ${toErrorMessage(error)}`);
      setCategories(DEMO_CATEGORIES);
      setQuality(DEMO_QUALITY);
    } finally {
      setBusy(false);
    }
  }, [push]);

  useEffect(() => {
    setIsDemo(isDemoMode());
    loadData();
  }, [loadData]);

  async function computeAllFeatures() {
    if (isDemoMode()) {
      push("Demo-Modus: Features wuerden neu berechnet");
      return;
    }
    setBusy(true);
    try {
      push("Starte Feature-Berechnung...");
      await apiFetch("/features/compute-all", { method: "POST" });
      push("Feature-Berechnung gestartet");
      setTimeout(loadData, 3000);
    } catch (error: unknown) {
      push(`Fehler: ${toErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    if (isDemoMode()) {
      setUploadStatus("Demo-Modus: Upload simuliert");
      push(`Demo: ${file.name} wuerde importiert`);
      setTimeout(() => setUploadStatus(null), 3000);
      return;
    }

    setUploadStatus("Uploading...");
    const formData = new FormData();
    formData.append("file", file);

    try {
      push(`Upload: ${file.name}...`);
      await apiFetch("/features/bulk-import", {
        method: "POST",
        body: formData,
        headers: {}, // Let browser set content-type for FormData
      });
      setUploadStatus("Upload erfolgreich!");
      push(`Import abgeschlossen: ${file.name}`);
      loadData();
    } catch (error: unknown) {
      setUploadStatus(`Fehler: ${toErrorMessage(error)}`);
      push(`Upload-Fehler: ${toErrorMessage(error)}`);
    }

    setTimeout(() => setUploadStatus(null), 5000);
  }

  const getImportanceColor = (value: number) => {
    if (value >= 0.85) return "var(--color-success)";
    if (value >= 0.7) return "var(--color-warning)";
    return "var(--color-text-muted)";
  };

  const getCoverageColor = (value: number) => {
    if (value >= 95) return "var(--color-success)";
    if (value >= 80) return "var(--color-warning)";
    return "var(--color-danger)";
  };

  return (
    <>
      {/* Page Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">ML Features</h1>
          <p className="subtitle">50+ Features fuer Fracht- und Preis-Prognosen</p>
        </div>
        <div className="pageHeaderActions">
          {isDemo && <Badge tone="warn">Demo-Modus</Badge>}
          <button className="btn" onClick={loadData} disabled={busy}>
            Aktualisieren
          </button>
          <button className="btn btnPrimary" onClick={computeAllFeatures} disabled={busy || isDemo}>
            Alle neu berechnen
          </button>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="kpiGrid">
        <div className="kpiCard">
          <span className="cardLabel">Gesamt Features</span>
          <span className="cardValue">{quality?.totalFeatures ?? "–"}</span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Durchschn. Coverage</span>
          <span className="cardValue" style={{ color: getCoverageColor(quality?.avgCoverage ?? 0) }}>
            {quality?.avgCoverage ? `${quality.avgCoverage.toFixed(1)}%` : "–"}
          </span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Durchschn. Importance</span>
          <span className="cardValue" style={{ color: getImportanceColor(quality?.avgImportance ?? 0) }}>
            {quality?.avgImportance ? quality.avgImportance.toFixed(2) : "–"}
          </span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Fehlende Datenpunkte</span>
          <span className="cardValue" style={{ color: (quality?.missingDataPoints ?? 0) > 0 ? "var(--color-warning)" : undefined }}>
            {quality?.missingDataPoints?.toLocaleString("de-DE") ?? "–"}
          </span>
        </div>
      </div>

      {/* Bulk Import */}
      <section className="panel" aria-labelledby="import-title" style={{ marginBottom: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 id="import-title" className="panelTitle">CSV Bulk Import</h2>
        </div>
        <div className="panelBody">
          <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
            Historische Fracht- oder Preisdaten als CSV importieren fuer ML-Training.
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              style={{ display: "none" }}
            />
            <button
              className="btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={isDemo}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17,8 12,3 7,8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              CSV hochladen
            </button>
            {uploadStatus && (
              <Badge tone={uploadStatus.includes("Fehler") ? "bad" : uploadStatus.includes("erfolgreich") ? "good" : "neutral"}>
                {uploadStatus}
              </Badge>
            )}
          </div>
          <p className="muted small" style={{ marginTop: "var(--space-3)" }}>
            Format: date, origin, destination, weight_kg, cost_eur, carrier (fuer Frachtdaten)
          </p>
        </div>
      </section>

      {/* Feature Categories */}
      {categories.map((category) => (
        <section key={category.name} className="panel" style={{ marginBottom: "var(--space-4)" }}>
          <div
            className="panelHeader"
            style={{ cursor: "pointer" }}
            onClick={() => setExpandedCategory(expandedCategory === category.name ? null : category.name)}
          >
            <h2 className="panelTitle" style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{
                  transform: expandedCategory === category.name ? "rotate(90deg)" : "rotate(0deg)",
                  transition: "transform 0.2s ease",
                }}
              >
                <polyline points="9,18 15,12 9,6" />
              </svg>
              {category.name}
            </h2>
            <Badge tone="neutral">{category.features.length} Features</Badge>
          </div>

          {expandedCategory === category.name && (
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Feature Name</th>
                    <th>Beschreibung</th>
                    <th>Typ</th>
                    <th>Importance</th>
                    <th>Coverage</th>
                    <th>Zuletzt berechnet</th>
                  </tr>
                </thead>
                <tbody>
                  {category.features.map((feature) => (
                    <tr key={feature.name}>
                      <td>
                        <code style={{ 
                          background: "var(--color-bg-muted)", 
                          padding: "2px 6px", 
                          borderRadius: "var(--radius-sm)",
                          fontSize: "var(--font-size-xs)"
                        }}>
                          {feature.name}
                        </code>
                      </td>
                      <td className="muted">{feature.description}</td>
                      <td>
                        <Badge tone="neutral">{feature.type}</Badge>
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                          <div style={{
                            width: 60,
                            height: 6,
                            background: "var(--color-bg-muted)",
                            borderRadius: "var(--radius-full)",
                            overflow: "hidden",
                          }}>
                            <div style={{
                              width: `${feature.importance * 100}%`,
                              height: "100%",
                              background: getImportanceColor(feature.importance),
                              borderRadius: "var(--radius-full)",
                            }} />
                          </div>
                          <span style={{ 
                            fontSize: "var(--font-size-xs)", 
                            color: getImportanceColor(feature.importance),
                            fontVariantNumeric: "tabular-nums",
                          }}>
                            {feature.importance.toFixed(2)}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span style={{ 
                          color: getCoverageColor(feature.coverage),
                          fontVariantNumeric: "tabular-nums",
                        }}>
                          {feature.coverage.toFixed(1)}%
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)" }}>
                        {feature.lastComputed}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ))}

      {/* Click to expand hint */}
      {categories.length > 0 && !expandedCategory && (
        <p className="muted" style={{ textAlign: "center", marginTop: "var(--space-4)" }}>
          Klicken Sie auf eine Kategorie um die Features anzuzeigen.
        </p>
      )}

      {/* Activity Log */}
      <section className="panel" aria-labelledby="log-title" style={{ marginTop: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 id="log-title" className="panelTitle">Aktivitaet</h2>
        </div>
        <div className="panelBody">
          <div className="codeBox" style={{ maxHeight: 150, overflowY: "auto" }}>
            {log.length > 0 ? (
              log.map((l, idx) => <div key={idx}>{l}</div>)
            ) : (
              <span className="muted">Noch keine Aktivitaeten.</span>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
