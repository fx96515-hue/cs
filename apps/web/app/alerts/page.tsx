"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import DataQualityMini from "../components/DataQualityMini";

/* ============================================================
   WARNUNGEN - ENTERPRISE VIEW
   ============================================================ */

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
  by_severity: {
    critical: number;
    warning: number;
    info: number;
  };
};

function DemoBanner() {
  return (
    <div className="alert warn" style={{ marginBottom: "var(--space-6)" }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <div>
        <div className="alertTitle">Demo-Modus aktiv</div>
        <div className="alertText">Es sind keine echten Daten verfügbar. Starte das Backend und melde dich mit echten Zugangsdaten an.</div>
      </div>
    </div>
  );
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<QualityAlert[]>([]);
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [filter, setFilter] = useState<{
    severity: string;
    acknowledged: string;
    entity_type: string;
  }>({ severity: "all", acknowledged: "false", entity_type: "all" });
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  const fetchAlerts = useCallback(async () => {
    if (isDemoMode()) {
      setIsDemo(true);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.severity !== "all") params.set("severity", filter.severity);
      if (filter.acknowledged !== "all") params.set("acknowledged", filter.acknowledged);
      if (filter.entity_type !== "all") params.set("entity_type", filter.entity_type);

      const qs = params.toString();
      const data = await apiFetch<QualityAlert[]>(`/alerts${qs ? `?${qs}` : ""}`);
      setAlerts(data);
    } catch (e) {
      if (e instanceof Error && e.message === "DEMO_MODE") {
        setIsDemo(true);
      } else {
        console.error("Fehler beim Laden der Warnungen:", e);
      }
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
      if (!(e instanceof Error && e.message === "DEMO_MODE")) {
        console.error("Fehler beim Laden der Zusammenfassung:", e);
      }
    }
  }, []);

  async function acknowledgeAlert(id: number) {
    if (isDemoMode()) return;
    try {
      await apiFetch(`/alerts/${id}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ acknowledged_by: "user" }),
      });
      void fetchAlerts();
      void fetchSummary();
    } catch (e) {
      console.error("Fehler beim Bestätigen der Warnung:", e);
    }
  }

  async function checkNow() {
    if (isDemoMode()) return;
    try {
      await apiFetch("/alerts/check-now", { method: "POST" });
      void fetchAlerts();
      void fetchSummary();
    } catch (e) {
      console.error("Fehler beim Prüfen der Warnungen:", e);
    }
  }

  useEffect(() => {
    setIsDemo(isDemoMode());
    void fetchAlerts();
    void fetchSummary();
  }, [fetchAlerts, fetchSummary]);

  const getSeverityBadge = (severity: string): { tone: "bad" | "warn" | "neutral"; label: string } => {
    const map: Record<string, { tone: "bad" | "warn" | "neutral"; label: string }> = {
      critical: { tone: "bad", label: "Kritisch" },
      warning: { tone: "warn", label: "Warnung" },
      info: { tone: "neutral", label: "Info" },
    };
    return map[severity] || { tone: "neutral", label: severity };
  };

  return (
    <div className="page">
      <div className="content">
        {/* Seitenheader */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Warnungen</h1>
            <p className="subtitle">
              Qualitäts- und Zertifizierungsänderungen überwachen
            </p>
          </div>
          <div className="pageHeaderActions">
            <button
              type="button"
              className="btn btnPrimary"
              onClick={checkNow}
              disabled={isDemo}
            >
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

        {/* Demo-Banner */}
        {isDemo && <DemoBanner />}

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
              <span className="cardValue">{summary.unacknowledged}</span>
              <span className="cardHint">Benötigen Aufmerksamkeit</span>
            </div>
            <div className="kpiCard">
              <span className="cardLabel">Kritisch</span>
              <span className="cardValue">{summary.by_severity.critical}</span>
              <span className="cardHint">Hohe Priorität</span>
            </div>
            <div className="kpiCard">
              <span className="cardLabel">Warnungen</span>
              <span className="cardValue">{summary.by_severity.warning}</span>
              <span className="cardHint">Mittlere Priorität</span>
            </div>
          </div>
        )}

        {/* Filter */}
        {!isDemo && (
          <div className="panel" style={{ marginBottom: "var(--space-6)" }}>
            <div className="panelHeader">
              <h2 className="panelTitle">Filter</h2>
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
                  <label className="fieldLabel">Schweregrad</label>
                  <select
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
                  <label className="fieldLabel">Status</label>
                  <select
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
                  <label className="fieldLabel">Entitätstyp</label>
                  <select
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
          </div>
        )}

        {/* Warnungstabelle */}
        {!isDemo && (
          <div className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Warnungsliste</h2>
              <span className="badge">{alerts.length} Einträge</span>
            </div>

            {loading ? (
              <div className="panelBody">
                <div className="loading">
                  <div className="spinner"></div>
                </div>
              </div>
            ) : alerts.length === 0 ? (
              <div className="panelBody">
                <div className="emptyState">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.3, marginBottom: "var(--space-4)" }}>
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                  </svg>
                  <h3 className="h4">Keine Warnungen</h3>
                  <p className="subtitle">
                    Keine Warnungen entsprechen den gewählten Filterkriterien.
                  </p>
                </div>
              </div>
            ) : (
              <div className="tableWrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Schweregrad</th>
                      <th>Typ</th>
                      <th>Entität</th>
                      <th>Feld</th>
                      <th>Änderung</th>
                      <th>Erstellt</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.map((alert) => {
                      const sev = getSeverityBadge(alert.severity);
                      return (
                        <tr key={alert.id}>
                          <td>
                            <Badge tone={sev.tone}>{sev.label}</Badge>
                          </td>
                          <td>
                            <Badge>
                              {alert.alert_type.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
                            </Badge>
                          </td>
                          <td>
                            <span className="small">
                              {alert.entity_type} #{alert.entity_id}
                            </span>
                          </td>
                          <td>{alert.field_name || "-"}</td>
                          <td>
                            {alert.old_value !== null && alert.new_value !== null ? (
                              <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--font-size-sm)" }}>
                                {alert.old_value.toFixed(1)} → {alert.new_value.toFixed(1)}
                                {alert.change_amount !== null && (
                                  <Badge
                                    tone={alert.change_amount > 0 ? "good" : "bad"}
                                    style={{ marginLeft: "var(--space-2)" }}
                                  >
                                    {alert.change_amount > 0 ? "+" : ""}
                                    {alert.change_amount.toFixed(1)}
                                  </Badge>
                                )}
                              </span>
                            ) : (
                              "-"
                            )}
                          </td>
                          <td>
                            <span className="small muted">
                              {new Date(alert.created_at).toLocaleDateString("de-DE")}
                            </span>
                          </td>
                          <td>
                            {!alert.acknowledged ? (
                              <button
                                className="btn btnSm"
                                onClick={() => acknowledgeAlert(alert.id)}
                              >
                                Bestätigen
                              </button>
                            ) : (
                              <Badge tone="good">
                                {alert.acknowledged_by || "Bestätigt"}
                              </Badge>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Datenqualität */}
        {!isDemo && (
          <div style={{ marginTop: "var(--space-6)" }}>
            <DataQualityMini title="Datenqualität" limit={10} />
          </div>
        )}
      </div>
    </div>
  );
}
