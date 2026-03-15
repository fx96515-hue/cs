"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import { toErrorMessage } from "../utils/error";

type DataSource = {
  name: string;
  provider: string;
  status: "online" | "degraded" | "offline" | "unknown";
  lastSync: string;
  recordCount: number;
  avgLatency: number;
  errorRate: number;
};

type PipelineStatus = {
  totalSources: number;
  online: number;
  degraded: number;
  offline: number;
  lastFullSync: string;
  nextScheduled: string;
};

// Demo data for the data sources
const DEMO_SOURCES: DataSource[] = [
  { name: "Coffee Prices", provider: "Yahoo Finance", status: "online", lastSync: "2026-03-14 09:00", recordCount: 15420, avgLatency: 120, errorRate: 0.1 },
  { name: "FX Rates (ECB)", provider: "ECB API", status: "online", lastSync: "2026-03-14 08:30", recordCount: 8920, avgLatency: 85, errorRate: 0 },
  { name: "FX Rates (OANDA)", provider: "OANDA", status: "online", lastSync: "2026-03-14 08:30", recordCount: 4560, avgLatency: 95, errorRate: 0.2 },
  { name: "Weather Peru", provider: "OpenMeteo", status: "online", lastSync: "2026-03-14 06:00", recordCount: 45600, avgLatency: 180, errorRate: 0.5 },
  { name: "Rainfall Data", provider: "RAIN4PE", status: "online", lastSync: "2026-03-14 06:00", recordCount: 12300, avgLatency: 250, errorRate: 1.2 },
  { name: "Satellite Weather", provider: "NASA GPM", status: "degraded", lastSync: "2026-03-13 18:00", recordCount: 8900, avgLatency: 450, errorRate: 5.8 },
  { name: "Peru Weather Stations", provider: "SENAMHI", status: "online", lastSync: "2026-03-14 00:00", recordCount: 3400, avgLatency: 320, errorRate: 2.1 },
  { name: "Shipping AIS", provider: "AIS Stream", status: "degraded", lastSync: "2026-03-14 05:45", recordCount: 12800, avgLatency: 380, errorRate: 4.5 },
  { name: "Port Data", provider: "MarineTraffic", status: "online", lastSync: "2026-03-14 07:00", recordCount: 2340, avgLatency: 210, errorRate: 0.8 },
  { name: "Market News", provider: "NewsAPI", status: "online", lastSync: "2026-03-14 07:15", recordCount: 2340, avgLatency: 95, errorRate: 0.3 },
  { name: "Social Sentiment", provider: "Twitter/Reddit", status: "online", lastSync: "2026-03-14 08:00", recordCount: 5670, avgLatency: 280, errorRate: 1.5 },
  { name: "Peru Statistics", provider: "INEI", status: "online", lastSync: "2026-03-13 00:00", recordCount: 890, avgLatency: 520, errorRate: 0 },
  { name: "Peru Central Bank", provider: "BCRP", status: "online", lastSync: "2026-03-13 00:00", recordCount: 1230, avgLatency: 380, errorRate: 0 },
  { name: "World Bank Data", provider: "World Bank API", status: "online", lastSync: "2026-03-10 00:00", recordCount: 450, avgLatency: 680, errorRate: 0 },
  { name: "Coffee Blogs", provider: "Web Scraper", status: "online", lastSync: "2026-03-14 04:00", recordCount: 780, avgLatency: 1200, errorRate: 3.2 },
  { name: "Freight Indices", provider: "Baltic Exchange", status: "offline", lastSync: "2026-03-12 00:00", recordCount: 340, avgLatency: 0, errorRate: 100 },
  { name: "Container Rates", provider: "Freightos", status: "online", lastSync: "2026-03-14 06:00", recordCount: 1560, avgLatency: 150, errorRate: 0.4 },
];

const DEMO_STATUS: PipelineStatus = {
  totalSources: 17,
  online: 14,
  degraded: 2,
  offline: 1,
  lastFullSync: "2026-03-14 06:00",
  nextScheduled: "2026-03-14 12:00",
};

export default function PipelinePage() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [filter, setFilter] = useState<"all" | "online" | "degraded" | "offline">("all");
  const [syncingSource, setSyncingSource] = useState<string | null>(null);

  const push = useCallback((line: string) => {
    setLog((prev) => [`${new Date().toLocaleTimeString()}  ${line}`, ...prev].slice(0, 50));
  }, []);

  const loadData = useCallback(async () => {
    if (isDemoMode()) {
      setIsDemo(true);
      setSources(DEMO_SOURCES);
      setStatus(DEMO_STATUS);
      return;
    }
    setBusy(true);
    try {
      const [sourcesRes, statusRes] = await Promise.all([
        apiFetch<DataSource[]>("/pipeline/sources"),
        apiFetch<PipelineStatus>("/pipeline/status"),
      ]);
      setSources(sourcesRes);
      setStatus(statusRes);
      push("Pipeline-Status geladen");
    } catch (error: unknown) {
      push(`Fehler: ${toErrorMessage(error)}`);
      // Fallback to demo data
      setSources(DEMO_SOURCES);
      setStatus(DEMO_STATUS);
    } finally {
      setBusy(false);
    }
  }, [push]);

  useEffect(() => {
    setIsDemo(isDemoMode());
    loadData();
  }, [loadData]);

  async function triggerSync(sourceName?: string) {
    if (isDemoMode()) {
      push(`Demo-Modus: ${sourceName || "Alle Quellen"} wuerden synchronisiert`);
      return;
    }
    
    if (sourceName) {
      setSyncingSource(sourceName);
    } else {
      setBusy(true);
    }
    
    try {
      const endpoint = sourceName 
        ? `/pipeline/trigger/${encodeURIComponent(sourceName)}`
        : "/pipeline/trigger-all";
      push(`Starte Sync: ${sourceName || "Alle Quellen"}...`);
      await apiFetch(endpoint, { method: "POST" });
      push(`Sync gestartet: ${sourceName || "Alle Quellen"}`);
      // Reload after a short delay
      setTimeout(loadData, 2000);
    } catch (error: unknown) {
      push(`Sync-Fehler: ${toErrorMessage(error)}`);
    } finally {
      setSyncingSource(null);
      setBusy(false);
    }
  }

  const filteredSources = sources.filter(s => {
    if (filter === "all") return true;
    return s.status === filter;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "online": return <Badge tone="good">Online</Badge>;
      case "degraded": return <Badge tone="warn">Eingeschraenkt</Badge>;
      case "offline": return <Badge tone="bad">Offline</Badge>;
      default: return <Badge tone="neutral">Unbekannt</Badge>;
    }
  };

  const getLatencyColor = (ms: number) => {
    if (ms === 0) return "var(--color-text-muted)";
    if (ms < 200) return "var(--color-success)";
    if (ms < 500) return "var(--color-warning)";
    return "var(--color-danger)";
  };

  const getErrorRateColor = (rate: number) => {
    if (rate === 0) return "var(--color-success)";
    if (rate < 2) return "var(--color-warning)";
    return "var(--color-danger)";
  };

  return (
    <div className="content">
      {/* Page Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Data Pipeline</h1>
          <p className="subtitle">17 Datenquellen - Echtzeit-Monitoring und Steuerung</p>
        </div>
        <div className="pageHeaderActions">
          {isDemo && <Badge tone="warn">Demo-Modus</Badge>}
          <button className="btn" onClick={loadData} disabled={busy}>
            Aktualisieren
          </button>
          <button className="btn btnPrimary" onClick={() => triggerSync()} disabled={busy || isDemo}>
            Alle synchronisieren
          </button>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="kpiGrid">
        <div className="kpiCard">
          <span className="cardLabel">Gesamt Quellen</span>
          <span className="cardValue">{status?.totalSources ?? "–"}</span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Online</span>
          <span className="cardValue" style={{ color: "var(--color-success)" }}>
            {status?.online ?? "–"}
          </span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Eingeschraenkt</span>
          <span className="cardValue" style={{ color: status?.degraded && status.degraded > 0 ? "var(--color-warning)" : undefined }}>
            {status?.degraded ?? "–"}
          </span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Offline</span>
          <span className="cardValue" style={{ color: status?.offline && status.offline > 0 ? "var(--color-danger)" : undefined }}>
            {status?.offline ?? "–"}
          </span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Letzter Full-Sync</span>
          <span className="cardValue" style={{ fontSize: "var(--font-size-lg)" }}>
            {status?.lastFullSync ?? "–"}
          </span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Naechster Sync</span>
          <span className="cardValue" style={{ fontSize: "var(--font-size-lg)" }}>
            {status?.nextScheduled ?? "–"}
          </span>
        </div>
      </div>

      {/* Sources Table */}
      <section className="panel" aria-labelledby="sources-title">
        <div className="panelHeader">
          <h2 id="sources-title" className="panelTitle">Datenquellen</h2>
          <div className="panelActions" style={{ display: "flex", gap: "var(--space-2)" }}>
            <select
              className="input"
              value={filter}
              onChange={(e) => setFilter(e.target.value as typeof filter)}
              style={{ width: 160, height: 32, fontSize: "var(--font-size-sm)" }}
              aria-label="Status filtern"
            >
              <option value="all">Alle Status</option>
              <option value="online">Nur Online</option>
              <option value="degraded">Nur Eingeschraenkt</option>
              <option value="offline">Nur Offline</option>
            </select>
          </div>
        </div>

        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Datenquelle</th>
                <th>Provider</th>
                <th>Status</th>
                <th>Letzter Sync</th>
                <th>Datensaetze</th>
                <th>Latenz (ms)</th>
                <th>Fehlerrate</th>
                <th>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {filteredSources.length > 0 ? (
                filteredSources.map((source) => (
                  <tr key={source.name}>
                    <td>
                      <strong>{source.name}</strong>
                    </td>
                    <td className="muted">{source.provider}</td>
                    <td>{getStatusBadge(source.status)}</td>
                    <td className="mono" style={{ fontSize: "var(--font-size-xs)" }}>
                      {source.lastSync}
                    </td>
                    <td style={{ fontVariantNumeric: "tabular-nums" }}>
                      {source.recordCount.toLocaleString("de-DE")}
                    </td>
                    <td style={{ color: getLatencyColor(source.avgLatency), fontVariantNumeric: "tabular-nums" }}>
                      {source.avgLatency > 0 ? `${source.avgLatency}ms` : "–"}
                    </td>
                    <td style={{ color: getErrorRateColor(source.errorRate), fontVariantNumeric: "tabular-nums" }}>
                      {source.errorRate.toFixed(1)}%
                    </td>
                    <td>
                      <button
                        className="btn btnSm"
                        onClick={() => triggerSync(source.name)}
                        disabled={syncingSource === source.name || isDemo}
                      >
                        {syncingSource === source.name ? "Sync..." : "Sync"}
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="tableEmpty">
                    Keine Datenquellen gefunden.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Activity Log */}
      <section className="panel" aria-labelledby="log-title" style={{ marginTop: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 id="log-title" className="panelTitle">Aktivitaetsprotokoll</h2>
        </div>
        <div className="panelBody">
          <div className="codeBox" style={{ maxHeight: 200, overflowY: "auto" }}>
            {log.length > 0 ? (
              log.map((l, idx) => <div key={idx}>{l}</div>)
            ) : (
              <span className="muted">Noch keine Aktivitaeten protokolliert.</span>
            )}
          </div>
        </div>
      </section>

      {/* Provider Legend */}
      <section className="panel" aria-labelledby="legend-title" style={{ marginTop: "var(--space-6)" }}>
        <div className="panelHeader">
          <h2 id="legend-title" className="panelTitle">Provider-Uebersicht</h2>
        </div>
        <div className="panelBody">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: "var(--space-4)" }}>
            <div>
              <h4 className="h4" style={{ marginBottom: "var(--space-2)" }}>Marktdaten</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                <li className="muted small">Yahoo Finance - Kaffee-Futures (CC=F)</li>
                <li className="muted small">ECB - EUR Wechselkurse</li>
                <li className="muted small">OANDA - Exotische Waehrungen</li>
              </ul>
            </div>
            <div>
              <h4 className="h4" style={{ marginBottom: "var(--space-2)" }}>Wetter & Klima</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                <li className="muted small">OpenMeteo - Globale Wetterdaten</li>
                <li className="muted small">RAIN4PE - Peru Niederschlag</li>
                <li className="muted small">NASA GPM - Satellitendaten</li>
                <li className="muted small">SENAMHI - Peru Wetterstationen</li>
              </ul>
            </div>
            <div>
              <h4 className="h4" style={{ marginBottom: "var(--space-2)" }}>Logistik</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                <li className="muted small">AIS Stream - Schiffsverfolgung</li>
                <li className="muted small">MarineTraffic - Hafendaten</li>
                <li className="muted small">Freightos - Containerpreise</li>
              </ul>
            </div>
            <div>
              <h4 className="h4" style={{ marginBottom: "var(--space-2)" }}>Nachrichten & Sentiment</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                <li className="muted small">NewsAPI - Marktnachrichten</li>
                <li className="muted small">Twitter/Reddit - Social Sentiment</li>
                <li className="muted small">Web Scraper - Kaffee-Blogs</li>
              </ul>
            </div>
            <div>
              <h4 className="h4" style={{ marginBottom: "var(--space-2)" }}>Peru Makrodaten</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                <li className="muted small">INEI - Nationale Statistiken</li>
                <li className="muted small">BCRP - Zentralbank Peru</li>
                <li className="muted small">World Bank - Handelsdaten</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
