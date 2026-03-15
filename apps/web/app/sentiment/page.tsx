"use client";

import { useEffect, useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import LineChart from "../charts/LineChart";
import Badge from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { ErrorPanel } from "../components/AlertError";
import { toErrorMessage } from "../utils/error";

type SentimentPoint = {
  id: number;
  region: string | null;
  entity_id: number | null;
  score: number;
  label: string;
  article_count: number;
  scored_at: string | null;
};

type SentimentResponse = {
  region: string | null;
  entity_id: number | null;
  data: SentimentPoint[];
  total: number;
};

const REGIONS = ["PE", "CO", "BR", "ET", "global"];

function labelTone(label: string): "good" | "warn" | "bad" | "neutral" {
  if (label === "positive") return "good";
  if (label === "negative") return "bad";
  return "neutral";
}

export default function SentimentPage() {
  const [region, setRegion] = useState("PE");
  const [data, setData] = useState<SentimentPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  async function load(r: string) {
    if (isDemoMode()) { setLoading(false); return; }
    setLoading(true);
    setErr(null);
    try {
      const res = await apiFetch<SentimentResponse>(`/sentiment/${encodeURIComponent(r)}`);
      setData(Array.isArray(res?.data) ? res.data : []);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
      setData([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(region);
  }, [region]);

  const chartData = (data ?? []).map((d) => ({
    date: d.scored_at ? new Date(d.scored_at).toLocaleDateString() : "-",
    score: d.score,
    articles: d.article_count,
  }));

  const latest = data.length > 0 ? data[data.length - 1] : null;

  return (
    <div className="content">
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <div className="h1">Sentiment-Analyse</div>
          <div className="muted">Marktsentiment pro Region aus News-Quellen.</div>
        </div>
      </header>

      {err && <ErrorPanel message={err} onRetry={() => load(region)} />}

      {/* Region-Filter */}
      <div className="panel" style={{ marginBottom: "var(--space-4)" }}>
        <div className="panelHeader">
          <div className="panelTitle">Region</div>
        </div>
        <div className="panelBody">
          <div className="pageActions" style={{ flexWrap: "wrap" }}>
            {REGIONS.map((r) => (
              <button
                key={r}
                className={r === region ? "btn btnPrimary" : "btn"}
                onClick={() => setRegion(r)}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Aktuell */}
      {latest && (
        <div className="panel" style={{ marginBottom: "var(--space-4)" }}>
          <div className="panelHeader">
            <div className="panelTitle">Aktuell — {region}</div>
          </div>
          <div className="panelBody">
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
              <div>
                <div className="fieldLabel">Score</div>
                <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: "var(--font-weight-bold)", fontFamily: "var(--font-mono)" }}>
                  {latest.score.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="fieldLabel">Label</div>
                <Badge tone={labelTone(latest.label)}>{latest.label}</Badge>
              </div>
              <div>
                <div className="fieldLabel">Artikel</div>
                <div>{latest.article_count}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trend-Chart */}
      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Sentiment-Trend</div>
        </div>
        <div className="panelBody">
          {loading ? (
            <div className="muted">Lädt...</div>
          ) : chartData.length === 0 ? (
            <EmptyState
              icon={
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              }
              title="Keine Daten"
              text={`Für die Region "${region}" sind keine Sentiment-Daten vorhanden.`}
            />
          ) : (
            <LineChart data={chartData} xKey="date" yKey="score" title="" color="#22c55e" />
          )}
        </div>
      </div>
    </div>
  );
}
