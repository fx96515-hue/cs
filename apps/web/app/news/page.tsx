"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

type NewsItem = {
  id: number;
  topic?: string | null;
  title: string;
  url: string;
  source?: string | null;
  published_at?: string | null;
  created_at?: string | null;
};

export default function NewsPage() {
  const [topic, setTopic] = useState("peru coffee");
  const [days, setDays] = useState(2);
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const d = await apiFetch<NewsItem[]>(`/news?topic=${encodeURIComponent(topic)}&days=${days}&limit=60`);
      setItems(d);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sorted = useMemo(() => {
    const copy = [...items];
    copy.sort((a, b) => (b.published_at ?? "").localeCompare(a.published_at ?? ""));
    return copy;
  }, [items]);

  async function refreshNow() {
    setRefreshing(true);
    setMsg(null);
    setErr(null);
    try {
      const r = await apiFetch<{ status: string; created?: number; updated?: number; errors?: any[] }>(
        `/news/refresh?topic=${encodeURIComponent(topic)}`,
        { method: "POST" }
      );
      setMsg(`Refresh: ${r.status}${typeof r.created === "number" ? ` • neu ${r.created}` : ""}${
        typeof r.updated === "number" ? ` • aktualisiert ${r.updated}` : ""
      }`);
      await load();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Marktradar</div>
          <div className="muted">News, Quellen, Themen – ein Ort.</div>
        </div>
        <div className="row gap">
          <button className="btn" onClick={load} disabled={loading || refreshing}>
            Neu laden
          </button>
          <button className="btn btnPrimary" onClick={refreshNow} disabled={refreshing}>
            {refreshing ? "Refresh…" : "Refresh (API)"}
          </button>
        </div>
      </div>

      {msg ? <div className="success">{msg}</div> : null}
      {err ? <div className="error">{err}</div> : null}

      <div className="panel" style={{ marginBottom: 14 }}>
        <div className="panelTitle">Filter</div>
        <div className="row gap" style={{ flexWrap: "wrap" }}>
          <div>
            <div className="label">Topic</div>
            <input className="input" value={topic} onChange={(e) => setTopic(e.target.value)} style={{ width: 320 }} />
          </div>
          <div>
            <div className="label">Tage</div>
            <input
              className="input"
              type="number"
              min={1}
              max={30}
              value={days}
              onChange={(e) => setDays(Number(e.target.value || 2))}
              style={{ width: 110 }}
            />
          </div>
          <div style={{ alignSelf: "end" }}>
            <button className="btn" onClick={load} disabled={loading || refreshing}>
              Anwenden
            </button>
          </div>
        </div>
        <div className="muted" style={{ marginTop: 10 }}>
          Tipp: Für Peru z.B. „peru specialty coffee“, „cajamarca coffee cooperative“, „peru arabica export“.
        </div>
      </div>

      <div className="panel">
        <div className="panelTitle">Ergebnisse ({sorted.length})</div>
        {loading ? (
          <div className="muted">Lade…</div>
        ) : sorted.length === 0 ? (
          <div className="muted">Keine Treffer.</div>
        ) : (
          <div className="list">
            {sorted.map((n) => (
              <a key={n.id} className="listItem" href={n.url} target="_blank" rel="noreferrer">
                <div className="listMain">
                  <div className="listTitle">{n.title}</div>
                  <div className="listMeta">
                    <span className="muted">{n.source ?? "(Quelle unbekannt)"}</span>
                    <span className="dot">•</span>
                    <span className="muted">{n.published_at ? new Date(n.published_at).toLocaleString() : "-"}</span>
                    <span className="dot">•</span>
                    <Badge tone="neutral">{n.topic ?? topic}</Badge>
                  </div>
                </div>
                <div className="listRight">↗</div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
