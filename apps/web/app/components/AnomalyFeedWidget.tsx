"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "./Badge";

type AnomalyAlert = {
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
  created_at: string;
};

export default function AnomalyFeedWidget() {
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [disabled, setDisabled] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isDemoMode()) {
      setLoading(false);
      return;
    }
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiFetch<AnomalyAlert[]>("/anomalies?acknowledged=false&limit=5");
        if (!alive) return;
        setAnomalies(Array.isArray(data) ? data : []);
      } catch (e: unknown) {
        if (!alive) return;
        if (e instanceof Error) {
          const match = e.message.match(/API error:\s*(\d{3})/);
          const status = match ? Number(match[1]) : undefined;
          if (status === 503 || status === 404) {
            setDisabled(true);
          } else {
            setError(e.message);
          }
        } else {
          setError(String(e));
        }
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  if (disabled) return null;

  const severityTone = (s: string): "bad" | "warn" | "neutral" =>
    s === "critical" ? "bad" : s === "warning" ? "warn" : "neutral";

  const fmtDate = (x: string) =>
    new Date(x).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });

  const entityLabel = (a: AnomalyAlert) => {
    if (a.alert_type === "score_anomaly") return `Score-Ausreisser — ${a.entity_type} #${a.entity_id}`;
    return `Preis-Ausreisser — ${a.field_name ?? a.entity_type}`;
  };

  return (
    <div className="panel">
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Anomalie-Feed</div>
          <div className="muted small">Score- und Preis-Ausreisser</div>
        </div>
        <Link className="link small" href="/alerts">Alle anzeigen →</Link>
      </div>

      <div className="panelBody" style={{ padding: 0 }}>
        {loading ? (
          <div className="muted small" style={{ padding: "var(--space-4)" }}>Lädt...</div>
        ) : error ? (
          <div className="muted small" style={{ padding: "var(--space-4)" }}>Verbindung nicht verfügbar.</div>
        ) : anomalies.length === 0 ? (
          <div className="empty" style={{ padding: "var(--space-4) var(--space-5)" }}>
            Keine offenen Anomalien
          </div>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {anomalies.map((a) => (
              <li key={a.id} className="listRow">
                <div className="listMain">
                  <div className="listTitle">{entityLabel(a)}</div>
                  <div className="listMeta">
                    {a.new_value !== null && (
                      <span>Wert: {a.new_value.toFixed(2)}</span>
                    )}
                    {a.change_amount !== null && (
                      <>
                        <span className="dot">·</span>
                        <span>
                          {a.alert_type === "price_anomaly"
                            ? `Z = ${a.change_amount.toFixed(2)}`
                            : `Score: ${a.change_amount.toFixed(3)}`}
                        </span>
                      </>
                    )}
                    <span className="dot">·</span>
                    <span>{fmtDate(a.created_at)}</span>
                  </div>
                </div>
                <Badge tone={severityTone(a.severity)}>{a.severity}</Badge>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
