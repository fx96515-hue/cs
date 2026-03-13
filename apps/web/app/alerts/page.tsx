"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";
import DataQualityMini from "../components/DataQualityMini";

/* ============================================================
   ALERTS - ENTERPRISE VIEW
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

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<QualityAlert[]>([]);
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [filter, setFilter] = useState<{
    severity: string;
    acknowledged: string;
    entity_type: string;
  }>({ severity: "all", acknowledged: "false", entity_type: "all" });
  const [loading, setLoading] = useState(true);

  const fetchAlerts = useCallback(async () => {
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
      console.error("Failed to fetch alerts:", e);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  const fetchSummary = useCallback(async () => {
    try {
      const data = await apiFetch<AlertSummary>("/alerts/summary");
      setSummary(data);
    } catch (e) {
      console.error("Failed to fetch summary:", e);
    }
  }, []);

  async function acknowledgeAlert(id: number) {
    try {
      await apiFetch(`/alerts/${id}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ acknowledged_by: "user" }),
      });
      void fetchAlerts();
      void fetchSummary();
    } catch (e) {
      console.error("Failed to acknowledge alert:", e);
    }
  }

  async function checkNow() {
    try {
      await apiFetch("/alerts/check-now", { method: "POST" });
      void fetchAlerts();
      void fetchSummary();
    } catch (e) {
      console.error("Failed to check alerts:", e);
    }
  }

  useEffect(() => {
    void fetchAlerts();
    void fetchSummary();
  }, [fetchAlerts, fetchSummary]);

  const getSeverityBadge = (severity: string): { className: string; label: string } => {
    const map: Record<string, { className: string; label: string }> = {
      critical: { className: "badgeErr", label: "Kritisch" },
      warning: { className: "badgeWarn", label: "Warnung" },
      info: { className: "badgeInfo", label: "Info" },
    };
    return map[severity] || { className: "badge", label: severity };
  };

  return (
    <div className="page">
      <div className="content">
        {/* Page Header */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Warnungen</h1>
            <p className="subtitle">
              Qualitaets- und Zertifizierungsaenderungen ueberwachen
            </p>
          </div>
          <div className="pageHeaderActions">
            <button type="button" className="btn btnPrimary" onClick={checkNow}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
                <path d="M16 21h5v-5"/>
              </svg>
              Jetzt pruefen
            </button>
          </div>
        </header>

        {/* Summary KPIs */}
        {summary && (
          <div className="kpiGrid">
            <div className="kpiCard">
              <span className="cardLabel">Warnungen Gesamt</span>
              <span className="cardValue">{summary.total_alerts}</span>
              <span className="cardHint">Alle Zeiten</span>
            </div>
            <div className="kpiCard">
              <span className="cardLabel">Unbestaetigt</span>
              <span className="cardValue">{summary.unacknowledged}</span>
              <span className="cardHint">Benoetigen Aufmerksamkeit</span>
            </div>
            <div className="kpiCard">
              <span className="cardLabel">Kritisch</span>
              <span className="cardValue">{summary.by_severity.critical}</span>
              <span className="cardHint">Hohe Prioritaet</span>
            </div>
            <div className="kpiCard">
              <span className="cardLabel">Warnungen</span>
              <span className="cardValue">{summary.by_severity.warning}</span>
              <span className="cardHint">Mittlere Prioritaet</span>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="panel" style={{ marginBottom: "var(--space-6)" }}>
          <div className="panelHeader">
            <h2 className="panelTitle">Filter</h2>
            <button
              type="button"
              className="btn btnSm btnGhost"
              onClick={() => setFilter({ severity: "all", acknowledged: "false", entity_type: "all" })}
            >
              Zuruecksetzen
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
                  <option value="false">Unbestaetigt</option>
                  <option value="true">Bestaetigt</option>
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

        {/* Alerts Table */}
        <div className="panel">
          <div className="panelHeader">
            <h2 className="panelTitle">Warnungen</h2>
            <span className="badge">{alerts.length} Eintraege</span>
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
                  Es liegen keine Warnungen vor, die den Filterkriterien entsprechen.
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
                    <th>Aenderung</th>
                    <th>Erstellt</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => {
                    const severityBadge = getSeverityBadge(alert.severity);
                    return (
                      <tr key={alert.id}>
                        <td>
                          <span className={`badge ${severityBadge.className}`}>
                            {severityBadge.label}
                          </span>
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
                                <span className={`badge ${alert.change_amount > 0 ? "badgeOk" : "badgeErr"}`} style={{ marginLeft: "var(--space-2)" }}>
                                  {alert.change_amount > 0 ? "+" : ""}
                                  {alert.change_amount.toFixed(1)}
                                </span>
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
                              Bestaetigen
                            </button>
                          ) : (
                            <span className="badge badgeOk">
                              {alert.acknowledged_by || "Bestaetigt"}
                            </span>
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

        {/* Data Quality Widget */}
        <div style={{ marginTop: "var(--space-6)" }}>
          <DataQualityMini title="Datenqualitaet (Alerts)" limit={10} />
        </div>
      </div>
    </div>
  );
}
