"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import DataQualityMini from "../components/DataQualityMini";

type QualityAlert = {
  id: number;
  entity_type: string;
  entity_id: number;
  alert_type: string;
  field_name: string | null;
  old_value: number | null;
  new_value: number | null;
  change_amount: number | null;
  severity: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
  created_at: string;
};

type AlertSummary = {
  total_alerts: number;
  unacknowledged: number;
  by_severity: { critical: number; warning: number; info: number };
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<QualityAlert[]>([]);
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [filter, setFilter] = useState({ severity: "all", acknowledged: "false", entity_type: "all" });
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  const fetchAlerts = useCallback(async () => {
    if (isDemoMode()) { setIsDemo(true); setLoading(false); return; }
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.severity !== "all") params.set("severity", filter.severity);
      if (filter.acknowledged !== "all") params.set("acknowledged", filter.acknowledged);
      if (filter.entity_type !== "all") params.set("entity_type", filter.entity_type);
      const qs = params.toString();
      const data = await apiFetch<QualityAlert[]>(`/alerts${qs ? `?${qs}` : ""}`);
      setAlerts(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Fehler beim Laden der Warnungen:", e);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  const fetchSummary = useCallback(async () => {
    if (isDemoMode()) return;
    try {
      const data = await apiFetch<AlertSummary>("/alerts/summary");
      setSummary(data);
    } catch (e) {
      console.error("Fehler beim Laden der Zusammenfassung:", e);
    }
  }, []);

  async function acknowledgeAlert(id: number) {
    if (isDemoMode()) return;
    try {
      await apiFetch(`/alerts/${id}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ acknowledged_by: "user" }),
      });
      await Promise.all([fetchAlerts(), fetchSummary()]);
    } catch (e) {
      console.error("Fehler beim Bestätigen der Warnung:", e);
    }
  }

  async function checkNow() {
    if (isDemoMode()) return;
    try {
      await apiFetch("/alerts/check-now", { method: "POST" });
      await Promise.all([fetchAlerts(), fetchSummary()]);
    } catch (e) {
      console.error("Fehler beim Prüfen der Warnungen:", e);
    }
  }

  useEffect(() => {
    setIsDemo(isDemoMode());
    Promise.all([fetchAlerts(), fetchSummary()]).catch((error: unknown) => {
      console.error("Failed to initialize alerts page:", error);
    });
  }, [fetchAlerts, fetchSummary]);

  const severityLabel: Record<string, string> = {
    critical: "Kritisch",
    warning: "Warnung",
    info: "Info",
  };
  const severityTone: Record<string, "bad" | "warn" | "neutral"> = {
    critical: "bad",
    warning: "warn",
    info: "neutral",
  };

  return (
    <>
      {/* Seitenheader */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Warnungen</h1>
          <p className="subtitle">Qualitäts- und Zertifizierungsänderungen überwachen</p>
        </div>
        <div className="pageHeaderActions">
          <button type="button" className="btn btnPrimary" onClick={checkNow} disabled={isDemo}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
              <path d="M16 21h5v-5"/>
            </svg>
            Jetzt prüfen
          </button>
        </div>
      </header>

      {/* Kennzahlen */}
      {summary && !isDemo && (
        <div className="kpiGrid">
          <div className="kpiCard">
            <span className="cardLabel">Warnungen gesamt</span>
            <span className="cardValue">{summary.total_alerts}</span>
            <span className="cardHint">Alle Zeiträume</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Unbestätigt</span>
            <span className="cardValue" style={{ color: summary.unacknowledged > 0 ? "var(--color-danger)" : undefined }}>
              {summary.unacknowledged}
            </span>
            <span className="cardHint">Benötigen Aufmerksamkeit</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Kritisch</span>
            <span className="cardValue">{summary.by_severity.critical}</span>
            <span className="cardHint">Hohe Priorität</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Warnhinweise</span>
            <span className="cardValue">{summary.by_severity.warning}</span>
            <span className="cardHint">Mittlere Priorität</span>
          </div>
        </div>
      )}

      {/* Filter */}
      <section className="panel" aria-labelledby="filter-title">
        <div className="panelHeader">
          <h2 id="filter-title" className="panelTitle">Filter</h2>
          <button
            type="button"
            className="btn btnSm btnGhost"
            onClick={() => setFilter({ severity: "all", acknowledged: "false", entity_type: "all" })}
          >
            Zurücksetzen
          </button>
        </div>
        <div className="panelBody">
          <div className="fieldGrid2">
            <div className="field">
              <label className="fieldLabel" htmlFor="severity-select">Schweregrad</label>
              <select
                id="severity-select"
                className="input"
                value={filter.severity}
                onChange={(e) => setFilter({ ...filter, severity: e.target.value })}
              >
                <option value="all">Alle</option>
                <option value="critical">Kritisch</option>
                <option value="warning">Warnung</option>
                <option value="info">Info</option>
              </select>
            </div>
            <div className="field">
              <label className="fieldLabel" htmlFor="status-select">Status</label>
              <select
                id="status-select"
                className="input"
                value={filter.acknowledged}
                onChange={(e) => setFilter({ ...filter, acknowledged: e.target.value })}
              >
                <option value="all">Alle</option>
                <option value="false">Unbestätigt</option>
                <option value="true">Bestätigt</option>
              </select>
            </div>
            <div className="field">
              <label className="fieldLabel" htmlFor="entity-select">Entitätstyp</label>
              <select
                id="entity-select"
                className="input"
                value={filter.entity_type}
                onChange={(e) => setFilter({ ...filter, entity_type: e.target.value })}
              >
                <option value="all">Alle</option>
                <option value="cooperative">Kooperative</option>
                <option value="roaster">Rösterei</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      {/* Warnungstabelle */}
      <section className="panel" aria-labelledby="alerts-title">
        <div className="panelHeader">
          <h2 id="alerts-title" className="panelTitle">Warnungsliste</h2>
          {!isDemo && <span className="badge neutral">{alerts.length} Einträge</span>}
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Schweregrad</th>
                <th>Typ</th>
                <th>Entität</th>
                <th>Feld</th>
                <th>Änderung</th>
                <th>Datum</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {isDemo ? (
                <tr><td colSpan={7} className="tableEmpty">Demo-Modus – keine Daten verfügbar.</td></tr>
              ) : loading ? (
                <tr><td colSpan={7} className="tableEmpty">Lädt...</td></tr>
              ) : alerts.length === 0 ? (
                <tr><td colSpan={7} className="tableEmpty">Keine Warnungen gefunden.</td></tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td>
                      <Badge tone={severityTone[alert.severity] ?? "neutral"}>
                        {severityLabel[alert.severity] ?? alert.severity}
                      </Badge>
                    </td>
                    <td>
                      <span className="small">
                        {alert.alert_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                      </span>
                    </td>
                    <td>
                      <span className="mono small">{alert.entity_type} #{alert.entity_id}</span>
                    </td>
                    <td>{alert.field_name || "–"}</td>
                    <td>
                      {alert.old_value !== null && alert.new_value !== null ? (
                        <span className="mono small">
                          {alert.old_value.toFixed(1)} → {alert.new_value.toFixed(1)}
                          {alert.change_amount !== null && (
                            <Badge tone={alert.change_amount > 0 ? "good" : "bad"} style={{ marginLeft: "var(--space-2)" }}>
                              {alert.change_amount > 0 ? "+" : ""}{alert.change_amount.toFixed(1)}
                            </Badge>
                          )}
                        </span>
                      ) : "–"}
                    </td>
                    <td className="small muted">
                      {new Date(alert.created_at).toLocaleDateString("de-DE")}
                    </td>
                    <td>
                      {!alert.acknowledged ? (
                        <button className="btn btnSm" onClick={() => acknowledgeAlert(alert.id)}>
                          Bestätigen
                        </button>
                      ) : (
                        <Badge tone="good">{alert.acknowledged_by || "Bestätigt"}</Badge>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Datenqualität */}
      {!isDemo && (
        <div style={{ marginTop: "var(--space-6)" }}>
          <DataQualityMini title="Datenqualität" limit={10} />
        </div>
      )}
    </>
  );
}
