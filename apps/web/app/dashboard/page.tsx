"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import KpiCard from "../components/KpiCard";
import Badge from "../components/Badge";
import MarketPriceWidget from "../components/MarketPriceWidget";
import AnomalyFeedWidget from "../components/AnomalyFeedWidget";

type ApiStatus = { status: string };

type MarketPoint = {
  value: number;
  unit?: string | null;
  currency?: string | null;
  observed_at: string;
};

type MarketSnapshot = Record<string, MarketPoint | null>;

type Paged<T> = { items: T[]; total: number };

type NewsItem = {
  id: number;
  topic: string;
  title: string;
  source?: string | null;
  url?: string | null;
  published_at?: string | null;
};

type Report = {
  id: number;
  name: string;
  kind: string;
  status: string;
  report_at: string;
};

function fmtDate(x?: string | null) {
  if (!x) return "–";
  const d = new Date(x);
  return d.toLocaleString("de-DE", { dateStyle: "medium", timeStyle: "short" });
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [health, setHealth] = useState<ApiStatus | null>(null);
  const [market, setMarket] = useState<MarketSnapshot | null>(null);
  const [coopsTotal, setCoopsTotal] = useState<number | null>(null);
  const [roastersTotal, setRoastersTotal] = useState<number | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setErr(null);

        const [h, m, coops, roasters, n, r] = await Promise.all([
          apiFetch<ApiStatus>("/health", { skipAuth: true }),
          apiFetch<MarketSnapshot>("/market/latest"),
          apiFetch<Paged<any> | any[]>("/cooperatives?limit=1"),
          apiFetch<Paged<any> | any[]>("/roasters?limit=1"),
          apiFetch<NewsItem[]>("/news?limit=6"),
          apiFetch<Report[]>("/reports?limit=6"),
        ]);

        if (!alive) return;
        setHealth(h);
        setMarket(m);
        // Handle both flat list and Paged format
        setCoopsTotal(Array.isArray(coops) ? coops.length : coops?.total ?? null);
        setRoastersTotal(Array.isArray(roasters) ? roasters.length : roasters?.total ?? null);
        setNews(Array.isArray(n) ? n : []);
        setReports(Array.isArray(r) ? r : []);
      } catch (e: any) {
        if (!alive) return;
        setErr(e?.message ?? String(e));
      } finally {
        if (!alive) return;
        setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  const fx = market?.["FX:USD_EUR"] ?? null;

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Übersicht</div>
          <div className="muted">
            Status, KPIs und die wichtigsten Signale auf einen Blick.
          </div>
        </div>
        <div className="actions">
          <Link className="btn" href="/ops">
            Ops & Jobs
          </Link>
          <button className="btn" onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      </div>

      {err ? (
        <div className="alert bad">
          <div className="alertTitle">Fehler beim Laden</div>
          <div className="alertText">{err}</div>
        </div>
      ) : null}

      <div className="gridKpi">
        <KpiCard
          label="Backend"
          value={
            <Badge tone={health?.status === "ok" ? "good" : "warn"}>
              {health?.status ?? (loading ? "…" : "unbekannt")}
            </Badge>
          }
          hint="/health"
        />
        <KpiCard
          label="Kooperativen"
          value={coopsTotal ?? (loading ? "…" : "–")}
          hint="Inventar im System"
        />
        <KpiCard
          label="Röstereien"
          value={roastersTotal ?? (loading ? "…" : "–")}
          hint="CRM-Pipeline"
        />
        <MarketPriceWidget />
        <KpiCard
          label="USD/EUR"
          value={fx ? fx.value.toFixed(4) : loading ? "…" : "–"}
          hint={fx ? `Stand: ${fmtDate(fx.observed_at)}` : "FX Feed"}
        />
      </div>

      <div className="grid2">
        <div className="panel">
          <div className="panelHeader">
            <div>
              <div className="panelTitle">Marktradar</div>
              <div className="muted">Neueste Headlines (Default: Peru Coffee)</div>
            </div>
            <Link className="link" href="/news">
              öffnen →
            </Link>
          </div>
          <div className="list">
            {(news ?? []).slice(0, 6).map((n) => (
              <div key={n.id} className="listRow">
                <div className="listMain">
                  <div className="listTitle">
                    {n.url ? (
                      <a className="link" href={n.url} target="_blank" rel="noreferrer">
                        {n.title}
                      </a>
                    ) : (
                      n.title
                    )}
                  </div>
                  <div className="listMeta">
                    <span>{n.source ?? "–"}</span>
                    <span className="dot">•</span>
                    <span>{fmtDate(n.published_at)}</span>
                  </div>
                </div>
                <Badge tone="neutral">{n.topic}</Badge>
              </div>
            ))}
            {(!news || news.length === 0) && !loading ? (
              <div className="empty">Noch keine News. In Ops → „News refresh“ starten.</div>
            ) : null}
          </div>
        </div>

        <div className="panel">
          <div className="panelHeader">
            <div>
              <div className="panelTitle">Reports & Runs</div>
              <div className="muted">Letzte Ingest-/Job-Reports</div>
            </div>
            <Link className="link" href="/reports">
              öffnen →
            </Link>
          </div>
          <div className="list">
            {(reports ?? []).slice(0, 6).map((r) => (
              <div key={r.id} className="listRow">
                <div className="listMain">
                  <div className="listTitle">{r.name}</div>
                  <div className="listMeta">
                    <span>{r.kind}</span>
                    <span className="dot">•</span>
                    <span>{fmtDate(r.report_at)}</span>
                  </div>
                </div>
                <Badge
                  tone={
                    r.status === "ok"
                      ? "good"
                      : r.status === "skipped"
                      ? "warn"
                      : r.status === "error"
                      ? "bad"
                      : "neutral"
                  }
                >
                  {r.status}
                </Badge>
              </div>
            ))}
            {(!reports || reports.length === 0) && !loading ? (
              <div className="empty">Noch keine Reports.</div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid2" style={{ marginTop: 14 }}>
        <AnomalyFeedWidget />
      </div>

      <div className="grid3">
        <div className="panel small">
          <div className="panelTitle">Nächste Schritte</div>
          <ol className="steps">
            <li>
              <b>Discovery Seed</b> ausführen (Ops) → Kooperativen/Röster initial füllen.
            </li>
            <li>
              <b>Enrichment</b> aktivieren → Webseiten/Infos ziehen → Scoring.
            </li>
            <li>
              <b>CRM</b> nutzen: Roasters → Outreach → Deals.
            </li>
          </ol>
        </div>
        <div className="panel small">
          <div className="panelTitle">Quick Links</div>
          <div className="chips">
            <Link className="chip" href="/cooperatives">
              Kooperativen
            </Link>
            <Link className="chip" href="/roasters">
              Röstereien
            </Link>
            <Link className="chip" href="/ops">
              Jobs / Ops
            </Link>
            <a className="chip" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
              API Docs (direct)
            </a>
          </div>
        </div>
        <div className="panel small">
          <div className="panelTitle">Hinweis</div>
          <div className="muted">
            Wenn „ui.localhost“/„api.localhost“ zicken: direkt nutzen:
            <div className="code">UI: http://localhost:3000 · API: http://localhost:8000/docs</div>
          </div>
        </div>
      </div>
    </div>
  );
}
