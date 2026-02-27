"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

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

  async function fetchAlerts() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.severity !== "all") params.set("severity", filter.severity);
      if (filter.acknowledged !== "all")
        params.set("acknowledged", filter.acknowledged);
      if (filter.entity_type !== "all")
        params.set("entity_type", filter.entity_type);

      const data = await apiFetch<QualityAlert[]>(`/alerts?${params}`);
      setAlerts(data);
    } catch (e) {
      console.error("Failed to fetch alerts:", e);
    } finally {
      setLoading(false);
    }
  }

  async function fetchSummary() {
    try {
      const data = await apiFetch<AlertSummary>("/alerts/summary");
      setSummary(data);
    } catch (e) {
      console.error("Failed to fetch summary:", e);
    }
  }

  async function acknowledgeAlert(id: number) {
    try {
      await apiFetch(`/alerts/${id}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ acknowledged_by: "user" }),
      });
      fetchAlerts();
      fetchSummary();
    } catch (e) {
      console.error("Failed to acknowledge alert:", e);
    }
  }

  async function checkNow() {
    try {
      await apiFetch("/alerts/check-now", { method: "POST" });
      fetchAlerts();
      fetchSummary();
    } catch (e) {
      console.error("Failed to check alerts:", e);
    }
  }

  useEffect(() => {
    fetchAlerts();
    fetchSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const severityBadge = (severity: string) => {
    const tone =
      severity === "critical" ? "bad" : severity === "warning" ? "warn" : "neutral";
    return <Badge tone={tone}>{severity}</Badge>;
  };

  const alertTypeBadge = (type: string) => {
    const label = type
      .replace("_", " ")
      .split(" ")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
    return <Badge tone="neutral">{label}</Badge>;
  };

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Warnungen</div>
          <div className="muted">Qualitäts- und Zertifizierungsänderungen überwachen</div>
        </div>
        <button className="btn btnPrimary" onClick={checkNow}>
          Jetzt prüfen
        </button>
      </div>

      {summary && (
        <div className="grid3" style={{ marginBottom: 20 }}>
          <div className="panel">
            <div className="statLabel">Gesamt</div>
            <div className="statValue">{summary.total_alerts}</div>
          </div>
          <div className="panel">
            <div className="statLabel">Unbestätigt</div>
            <div className="statValue">{summary.unacknowledged}</div>
          </div>
          <div className="panel">
            <div className="statLabel">Nach Schweregrad</div>
            <div className="row gap" style={{ marginTop: 8 }}>
              <div>
                <Badge tone="bad">Kritisch: {summary.by_severity.critical}</Badge>
              </div>
              <div>
                <Badge tone="warn">Warnung: {summary.by_severity.warning}</Badge>
              </div>
              <div>
                <Badge tone="neutral">Info: {summary.by_severity.info}</Badge>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="panelTitle">Filter</div>
        <div className="row gap" style={{ flexWrap: "wrap" }}>
          <div>
            <div className="label">Schweregrad</div>
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
          <div>
            <div className="label">Status</div>
            <select
              className="input"
              value={filter.acknowledged}
              onChange={(e) =>
                setFilter({ ...filter, acknowledged: e.target.value })
              }
            >
              <option value="all">Alle</option>
              <option value="false">Unbestätigt</option>
              <option value="true">Bestätigt</option>
            </select>
          </div>
          <div>
            <div className="label">Entitätstyp</div>
            <select
              className="input"
              value={filter.entity_type}
              onChange={(e) =>
                setFilter({ ...filter, entity_type: e.target.value })
              }
            >
              <option value="all">Alle</option>
              <option value="cooperative">Kooperative</option>
              <option value="roaster">Rösterei</option>
            </select>
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 14 }}>
        <div className="panelTitle">Warnungen ({alerts.length})</div>
        {loading ? (
          <div className="muted">Lädt...</div>
        ) : alerts.length === 0 ? (
          <div className="muted">Keine Warnungen gefunden.</div>
        ) : (
          <div className="table">
            <table>
              <thead>
                <tr>
                  <th>Schweregrad</th>
                  <th>Typ</th>
                  <th>Entität</th>
                  <th>Feld</th>
                  <th>Änderung</th>
                  <th>Erstellt</th>
                  <th>Aktion</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td>{severityBadge(alert.severity)}</td>
                    <td>{alertTypeBadge(alert.alert_type)}</td>
                    <td>
                      {alert.entity_type} #{alert.entity_id}
                    </td>
                    <td>{alert.field_name || "-"}</td>
                    <td>
                      {alert.old_value !== null && alert.new_value !== null ? (
                        <span>
                          {alert.old_value.toFixed(1)} → {alert.new_value.toFixed(1)}{" "}
                          {alert.change_amount !== null && (
                            <span
                              className={
                                alert.change_amount > 0 ? "good" : "bad"
                              }
                            >
                              ({alert.change_amount > 0 ? "+" : ""}
                              {alert.change_amount.toFixed(1)})
                            </span>
                          )}
                        </span>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>{new Date(alert.created_at).toLocaleDateString("de-DE")}</td>
                    <td>
                      {!alert.acknowledged ? (
                        <button
                          className="btn btnSmall"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          Bestätigen
                        </button>
                      ) : (
                        <span className="muted">
                          ✓ {alert.acknowledged_by || "Bestätigt"}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
