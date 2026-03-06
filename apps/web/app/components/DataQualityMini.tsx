import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "./Badge";
import { DataQualityFlag } from "../types";

type Props = {
  title?: string;
  limit?: number;
};

export default function DataQualityMini({ title = "Data Quality", limit = 12 }: Props) {
  const [flags, setFlags] = useState<DataQualityFlag[]>([]);
  const [severity, setSeverity] = useState("all");
  const [entityType, setEntityType] = useState("all");
  const [includeResolved, setIncludeResolved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(limit));
      if (severity !== "all") params.set("severity", severity);
      if (entityType !== "all") params.set("entity_type", entityType);
      if (includeResolved) params.set("include_resolved", "true");
      const data = await apiFetch<DataQualityFlag[]>(`/data-quality/flags?${params.toString()}`);
      setFlags(data);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [severity, entityType, includeResolved]);

  const severityTone = (s: string) =>
    s === "critical" ? "bad" : s === "warning" ? "warn" : "neutral";

  return (
    <div className="panel">
      <div className="panelHeader">
        <div>
          <div className="panelTitle">{title}</div>
          <div className="muted">Offene Data-Quality-Flags</div>
        </div>
        <button className="btn" onClick={load} disabled={loading}>
          Refresh
        </button>
      </div>

      <div className="row gap" style={{ marginBottom: 10, flexWrap: "wrap" }}>
        <select
          className="input"
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          style={{ width: 160 }}
        >
          <option value="all">Severity: alle</option>
          <option value="critical">critical</option>
          <option value="warning">warning</option>
          <option value="info">info</option>
        </select>
        <select
          className="input"
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
          style={{ width: 180 }}
        >
          <option value="all">Entity: alle</option>
          <option value="cooperative">cooperative</option>
          <option value="roaster">roaster</option>
          <option value="lot">lot</option>
          <option value="shipment">shipment</option>
        </select>
        <label className="row" style={{ gap: 6 }}>
          <input
            type="checkbox"
            checked={includeResolved}
            onChange={(e) => setIncludeResolved(e.target.checked)}
          />
          <span className="small muted">Resolved anzeigen</span>
        </label>
      </div>

      {err ? <div className="muted">Fehler: {err}</div> : null}

      {loading ? (
        <div className="muted">Laedt...</div>
      ) : flags.length === 0 ? (
        <div className="muted">Keine Flags.</div>
      ) : (
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Entity</th>
                <th>Feld</th>
                <th>Severity</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {flags.map((f) => (
                <tr key={f.id}>
                  <td className="mono">
                    {f.entity_type} #{f.entity_id}
                  </td>
                  <td>{f.field_name || "-"}</td>
                  <td>
                    <Badge tone={severityTone(f.severity)}>{f.severity}</Badge>
                  </td>
                  <td>{f.resolved_at ? "resolved" : "open"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
