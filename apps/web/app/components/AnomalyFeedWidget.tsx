"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
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
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiFetch<AnomalyAlert[]>(
          "/anomalies?acknowledged=false&limit=5"
        );
        if (!alive) return;
        setAnomalies(Array.isArray(data) ? data : []);
      } catch (e: unknown) {
        if (!alive) return;
        if (e instanceof Error) {
          // Detect feature-flag disabled via HTTP 503 status in error message
          const match = e.message.match(/API error:\s*(\d{3})/);
          const status = match ? Number(match[1]) : undefined;
          if (status === 503) {
            setDisabled(true);
          } else {
            setError(e.message);
          }
        } else {
          setError(String(e));
        }
      } finally {
        if (!alive) return;
        setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (disabled) return null;

  const severityTone = (s: string): "bad" | "warn" | "neutral" =>
    s === "critical" ? "bad" : s === "warning" ? "warn" : "neutral";

  const fmtDate = (x: string) =>
    new Date(x).toLocaleDateString("de-DE");

  return (
    <div className="panel">
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Anomalie-Feed</div>
          <div className="muted">Score- &amp; Preis-Ausreißer</div>
        </div>
        <Link className="link" href="/alerts">
          öffnen →
        </Link>
      </div>
      <div className="list">
        {loading ? (
          <div className="muted">Lädt…</div>
        ) : error ? (
          <div className="muted">Fehler: {error}</div>
        ) : anomalies.length === 0 ? (
          <div className="empty">Keine offenen Anomalien.</div>
        ) : (
          anomalies.map((a) => (
            <div key={a.id} className="listRow">
              <div className="listMain">
                <div className="listTitle">
                  {a.alert_type === "score_anomaly"
                    ? `Score-Ausreißer: ${a.entity_type} #${a.entity_id}`
                    : `Preis-Ausreißer: ${a.field_name ?? a.entity_type}`}
                </div>
                <div className="listMeta">
                  {a.new_value !== null && (
                    <span>Wert: {a.new_value.toFixed(2)}</span>
                  )}
                  {a.change_amount !== null && (
                    <>
                      <span className="dot">•</span>
                      <span>
                        {a.alert_type === "price_anomaly"
                          ? `Z=${a.change_amount.toFixed(2)}`
                          : `Score: ${a.change_amount.toFixed(3)}`}
                      </span>
                    </>
                  )}
                  <span className="dot">•</span>
                  <span>{fmtDate(a.created_at)}</span>
                </div>
              </div>
              <Badge tone={severityTone(a.severity)}>{a.severity}</Badge>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
