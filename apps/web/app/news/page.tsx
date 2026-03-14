"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import DataQualityMini from "../components/DataQualityMini";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { ErrorPanel } from "../components/AlertError";
import { useToast } from "../components/ToastProvider";
import { toErrorMessage } from "../utils/error";

type NewsItem = {
  id: number;
  topic: string | null;
  title: string;
  url: string;
  source: string | null;
  published_at: string | null;
  created_at: string | null;
};

export default function NewsPage() {
  const toast = useToast();
  const [topic, setTopic] = useState("peru coffee");
  const [days, setDays] = useState(2);
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (isDemoMode()) { setLoading(false); return; }
    setLoading(true);
    setErr(null);
    try {
      const d = await apiFetch<NewsItem[]>(
        `/news?topic=${encodeURIComponent(topic)}&days=${days}&limit=60`,
      );
      setItems(Array.isArray(d) ? d : []);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [days, topic]);

  useEffect(() => {
    load();
  }, [load]);

  const sorted = useMemo(() => {
    const copy = [...items];
    copy.sort((a, b) => (b.published_at ?? "").localeCompare(a.published_at ?? ""));
    return copy;
  }, [items]);

  async function refreshNow() {
    setRefreshing(true);
    setErr(null);
    try {
      const r = await apiFetch<{
        status: string;
        created: number;
        updated: number;
        errors: unknown[];
      }>(
        `/news/refresh?topic=${encodeURIComponent(topic)}`,
        { method: "POST" },
      );
      const parts = [`Refresh: ${r.status}`];
      if (typeof r.created === "number") parts.push(`neu ${r.created}`);
      if (typeof r.updated === "number") parts.push(`aktualisiert ${r.updated}`);
      toast.success(parts.join(" | "));
      await load();
    } catch (error: unknown) {
      toast.error(toErrorMessage(error));
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="content">
      <div className="pageHeader">
        <div>
          <div className="h1">Marktradar</div>
          <div className="muted">News, Quellen, Themen — ein Ort.</div>
        </div>
        <div className="pageActions">
          <button className="btn" onClick={load} disabled={loading || refreshing}>
            Neu laden
          </button>
          <button className="btn btnPrimary" onClick={refreshNow} disabled={refreshing}>
            {refreshing ? "Refresh..." : "Refresh (API)"}
          </button>
        </div>
      </div>

      {err && <ErrorPanel message={err} onRetry={load} />}

      {/* Filter */}
      <div className="panel" style={{ marginBottom: "var(--space-4)" }}>
        <div className="panelHeader">
          <div className="panelTitle">Filter</div>
        </div>
        <div className="panelBody">
          <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", alignItems: "flex-end" }}>
            <div className="field">
              <label className="fieldLabel">Topic</label>
              <input
                className="input"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                style={{ width: 320 }}
              />
            </div>
            <div className="field">
              <label className="fieldLabel">Tage</label>
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
            <button className="btn" onClick={load} disabled={loading || refreshing}>
              Anwenden
            </button>
          </div>
          <div className="muted" style={{ marginTop: "var(--space-3)" }}>
            Tipp: Für Peru z.B. &quot;peru specialty coffee&quot;,
            &quot;cajamarca coffee cooperative&quot;, &quot;peru arabica export&quot;.
          </div>
        </div>
      </div>

      {/* Ergebnisse */}
      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Ergebnisse</div>
          <span className="badge">{sorted.length} Artikel</span>
        </div>
        {loading ? (
          <SkeletonRows rows={6} cols={3} />
        ) : sorted.length === 0 ? (
          <EmptyState
            icon={
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
            }
            title="Keine Treffer"
            text={`Für das Thema "${topic}" wurden keine Artikel in den letzten ${days} Tagen gefunden.`}
          />
        ) : (
          <div className="list">
            {sorted.map((n) => (
              <a key={n.id} className="listItem" href={n.url} target="_blank" rel="noreferrer">
                <div className="listMain">
                  <div className="listTitle">{n.title}</div>
                  <div className="listMeta">
                    <span>{n.source ?? "(Quelle unbekannt)"}</span>
                    <span className="dot">·</span>
                    <span>
                      {n.published_at ? new Date(n.published_at).toLocaleString("de-DE") : "-"}
                    </span>
                    <span className="dot">·</span>
                    <Badge tone="neutral">{n.topic ?? topic}</Badge>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>

      <div style={{ marginTop: "var(--space-5)" }}>
        <DataQualityMini title="Data Quality (News Kontext)" limit={10} />
      </div>
    </div>
  );
}
