"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import KpiCard from "../components/KpiCard";
import Badge from "../components/Badge";
import MarketPriceWidget from "../components/MarketPriceWidget";
import AnomalyFeedWidget from "../components/AnomalyFeedWidget";
import { ErrorPanel } from "../components/AlertError";
import { toErrorMessage } from "../utils/error";

/* ============================================================
   TYPES
   ============================================================ */

type ApiStatus = { status: string };
type MarketPoint = { value: number; unit?: string | null; currency?: string | null; observed_at: string };
type MarketSnapshot = Record<string, MarketPoint | null>;
type Paged<T> = { items: T[]; total: number };
type InventoryRow = Record<string, unknown>;
type NewsItem = { id: number; topic: string; title: string; source?: string | null; url?: string | null; published_at?: string | null };
type Report = { id: number; name: string; kind: string; status: string; report_at: string };
type OpsOverview = { data_quality?: { open_flags?: number; critical_flags?: number } };

/* ============================================================
   HELPERS
   ============================================================ */

function fmtDate(x?: string | null) {
  if (!x) return "-";
  const d = new Date(x);
  return d.toLocaleString("de-DE", { dateStyle: "medium", timeStyle: "short" });
}

/* ============================================================
   ICONS
   ============================================================ */

const RefreshIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1.5 8a6.5 6.5 0 1 1 1.28 3.87" />
    <path d="M1.5 12V8h4" />
  </svg>
);

const ArrowRightIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 7h12M8 2l5 5-5 5" />
  </svg>
);

const ExternalIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 3L3 9M9 3H5M9 3v4" />
  </svg>
);

/* ============================================================
   DASHBOARD COMPONENT
   ============================================================ */

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [health, setHealth] = useState<ApiStatus | null>(null);
  const [market, setMarket] = useState<MarketSnapshot | null>(null);
  const [coopsTotal, setCoopsTotal] = useState<number | null>(null);
  const [roastersTotal, setRoastersTotal] = useState<number | null>(null);
  const [opsOverview, setOpsOverview] = useState<OpsOverview | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [reports, setReports] = useState<Report[]>([]);

  const loadData = async () => {
    try {
      setLoading(true);
      setErr(null);

      const [h, m, coops, roasters, n, r, ops] = await Promise.all([
        apiFetch<ApiStatus>("/health", { skipAuth: true }),
        apiFetch<MarketSnapshot>("/market/latest"),
        apiFetch<Paged<InventoryRow> | InventoryRow[]>("/cooperatives?limit=1"),
        apiFetch<Paged<InventoryRow> | InventoryRow[]>("/roasters?limit=1"),
        apiFetch<NewsItem[]>("/news?limit=5"),
        apiFetch<Report[]>("/reports?limit=5"),
        apiFetch<OpsOverview>("/ops/overview"),
      ]);

      setHealth(h);
      setMarket(m);
      setCoopsTotal(Array.isArray(coops) ? coops.length : coops?.total ?? null);
      setRoastersTotal(Array.isArray(roasters) ? roasters.length : roasters?.total ?? null);
      setNews(Array.isArray(n) ? n : []);
      setReports(Array.isArray(r) ? r : []);
      setOpsOverview(ops);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const fx = market?.["FX:USD_EUR"] ?? null;
  const criticalFlags = opsOverview?.data_quality?.critical_flags ?? 0;

  return (
    <div className="content">
      {/* Page Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Dashboard Übersicht</h1>
          <p className="subtitle">Systemstatus, Kennzahlen und wichtige Signale auf einen Blick.</p>
        </div>
        <div className="pageHeaderActions">
          <Link href="/ops" className="btn">
            Betrieb & Jobs
          </Link>
          <button className="btn" onClick={loadData} disabled={loading}>
            <RefreshIcon />
            <span>Aktualisieren</span>
          </button>
        </div>
      </header>

      {/* Error State */}
      {err && <ErrorPanel message={err} onRetry={loadData} />}

      {/* KPI Grid */}
      <section className="kpiGrid" aria-label="Kennzahlen">
        <KpiCard
          label="Systemstatus"
          value={
            <Badge tone={health?.status === "ok" ? "good" : "warn"}>
              {health?.status ?? (loading ? "..." : "unbekannt")}
            </Badge>
          }
          hint="Backend Health Check"
        />
        <KpiCard
          label="Kooperativen"
          value={coopsTotal ?? (loading ? "..." : "-")}
          hint="Aktive Lieferanten im System"
        />
        <KpiCard
          label="Röstereien"
          value={roastersTotal ?? (loading ? "..." : "-")}
          hint="Kaufbereite Kunden gesamt"
        />
        <KpiCard
          label="Datenqualität"
          value={
            <Link href="/ops?severity=critical">
              <Badge tone={criticalFlags > 0 ? "bad" : "good"}>
                {criticalFlags > 0 ? `${criticalFlags} kritisch` : "OK"}
              </Badge>
            </Link>
          }
          hint="Offene Warnungen"
        />
        <MarketPriceWidget />
        <KpiCard
          label="USD/EUR"
          value={fx ? fx.value.toFixed(4) : loading ? "..." : "-"}
          hint={fx ? `Stand: ${fmtDate(fx.observed_at)}` : "Wechselkurs"}
        />
      </section>

      {/* Main Content */}
      <div className="grid2">
        {/* Market Radar */}
        <section className="panel" aria-labelledby="news-title">
          <div className="panelHeader">
            <h2 id="news-title" className="panelTitle">Marktradar</h2>
            <Link href="/news" className="link small">
              Alle anzeigen <ArrowRightIcon />
            </Link>
          </div>
          <div className="panelBody">
            {news.length > 0 ? (
              <div className="list">
                {news.slice(0, 5).map((n) => (
                  <div key={n.id} className="listItem">
                    <div className="listMain">
                      {n.url ? (
                        <a className="listTitle link" href={n.url} target="_blank" rel="noreferrer">
                          {n.title}
                          <ExternalIcon />
                        </a>
                      ) : (
                        <div className="listTitle">{n.title}</div>
                      )}
                      <div className="listMeta">
                        <span>{n.source ?? "-"}</span>
                        <span className="dot">•</span>
                        <span>{fmtDate(n.published_at)}</span>
                      </div>
                    </div>
                    <Badge tone="neutral">{n.topic}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty">
                <p className="emptyText">Noch keine Marktnews verfügbar. Starte in der Betriebsseite den &quot;Marktnews aktualisieren&quot; Job.</p>
              </div>
            )}
          </div>
        </section>

        {/* Reports */}
        <section className="panel" aria-labelledby="reports-title">
          <div className="panelHeader">
            <h2 id="reports-title" className="panelTitle">Berichte & Jobs</h2>
            <Link href="/reports" className="link small">
              Alle anzeigen <ArrowRightIcon />
            </Link>
          </div>
          <div className="panelBody">
            {reports.length > 0 ? (
              <div className="list">
                {reports.slice(0, 5).map((r) => (
                  <div key={r.id} className="listItem">
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
                        r.status === "ok" ? "good" :
                        r.status === "skipped" ? "warn" :
                        r.status === "error" ? "bad" : "neutral"
                      }
                    >
                      {r.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty">
                <p className="emptyText">Noch keine Berichte vorhanden.</p>
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Anomaly Feed */}
      <AnomalyFeedWidget />

      {/* Quick Actions */}
      <section className="grid3" style={{ marginTop: "var(--space-6)" }}>
        <div className="card">
          <h3 className="h4" style={{ marginBottom: "var(--space-4)" }}>Nächste Schritte</h3>
          <ol className="steps">
            <li><b>Ersterfassung</b> durchführen - Kooperativen und Röstereien initial eintragen.</li>
            <li><b>Datenanreicherung</b> aktivieren - Webseiten analysieren, Bewertungen berechnen.</li>
            <li><b>CRM nutzen</b> - Röstereien pflegen, Anfragen starten, Abschlüsse nachverfolgen.</li>
          </ol>
        </div>

        <div className="card">
          <h3 className="h4" style={{ marginBottom: "var(--space-4)" }}>Schnellzugriff</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            <Link className="btn btnFull" href="/cooperatives">Kooperativen</Link>
            <Link className="btn btnFull" href="/roasters">Röstereien</Link>
            <Link className="btn btnFull" href="/shipments">Sendungen</Link>
          </div>
        </div>

        <div className="card">
          <h3 className="h4" style={{ marginBottom: "var(--space-4)" }}>Entwicklung</h3>
          <p className="small muted" style={{ marginBottom: "var(--space-3)" }}>
            Direkter Zugriff auf die Systeme:
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            <div className="code">Benutzeroberfläche: localhost:3000</div>
            <div className="code">Backend-API: localhost:8000</div>
          </div>
        </div>
      </section>
    </div>
  );
}
