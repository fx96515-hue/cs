"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import LineChart from "../charts/LineChart";
import Badge from "../components/Badge";

type SentimentPoint = {
  id: number;
  region?: string | null;
  entity_id?: number | null;
  score: number;
  label: string;
  article_count: number;
  scored_at?: string | null;
};

type SentimentResponse = {
  region?: string | null;
  entity_id?: number | null;
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
    setLoading(true);
    setErr(null);
    try {
      const res = await apiFetch<SentimentResponse>(`/sentiment/${encodeURIComponent(r)}`);
      setData(res.data);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
      setData([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(region);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [region]);

  const chartData = data.map((d) => ({
    date: d.scored_at ? new Date(d.scored_at).toLocaleDateString() : "-",
    score: d.score,
    articles: d.article_count,
  }));

  const latest = data.length > 0 ? data[data.length - 1] : null;

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Sentiment-Analyse</div>
          <div className="muted">Marktsentiment pro Region aus News-Quellen.</div>
        </div>
      </div>

      {err && <div className="error">{err}</div>}

      <div className="panel" style={{ marginBottom: 14 }}>
        <div className="panelTitle">Region</div>
        <div className="row gap" style={{ flexWrap: "wrap" }}>
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

      {latest && (
        <div className="panel" style={{ marginBottom: 14 }}>
          <div className="panelTitle">Aktuell – {region}</div>
          <div className="row gap">
            <div>
              <span className="label">Score</span>
              <span style={{ fontSize: 24, fontWeight: 700, marginLeft: 8 }}>
                {latest.score.toFixed(2)}
              </span>
            </div>
            <Badge tone={labelTone(latest.label)}>{latest.label}</Badge>
            <div className="muted">{latest.article_count} Artikel</div>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="panelTitle">Sentiment-Trend</div>
        {loading ? (
          <div className="muted">Lade…</div>
        ) : chartData.length === 0 ? (
          <div className="muted">Keine Daten für diese Region.</div>
        ) : (
          <LineChart data={chartData} xKey="date" yKey="score" title="" color="#22c55e" />
        )}
      </div>
    </div>
  );
}
