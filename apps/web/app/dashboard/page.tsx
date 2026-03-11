"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import KpiCard from "../components/KpiCard";
import Badge from "../components/Badge";
import MarketPriceWidget from "../components/MarketPriceWidget";
import AnomalyFeedWidget from "../components/AnomalyFeedWidget";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";

// ============================================================================
// Types
// ============================================================================

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

type OpsOverview = {
  data_quality?: {
    open_flags?: number;
    critical_flags?: number;
  };
};

// ============================================================================
// Helper Functions
// ============================================================================

function fmtDate(x?: string | null) {
  if (!x) return "-";
  const d = new Date(x);
  return d.toLocaleString("de-DE", { dateStyle: "medium", timeStyle: "short" });
}

function fmtDateShort(x?: string | null) {
  if (!x) return "-";
  const d = new Date(x);
  return d.toLocaleString("de-DE", { dateStyle: "short" });
}

// ============================================================================
// Sub-Components
// ============================================================================

function SystemHealthSection({
  health,
  opsOverview,
  loading,
}: {
  health: ApiStatus | null;
  opsOverview: OpsOverview | null;
  loading: boolean;
}) {
  const criticalFlags = opsOverview?.data_quality?.critical_flags ?? 0;
  const openFlags = opsOverview?.data_quality?.open_flags ?? 0;

  return (
    <div className="panel" style={{ marginBottom: 18 }}>
      <div className="panelHeader">
        <div>
          <div className="panelTitle">System & Datenqualitaet</div>
          <div className="muted small">Status-Uebersicht aller Systeme</div>
        </div>
        <Link className="link small" href="/ops">
          Ops oeffnen
        </Link>
      </div>
      <div className="panelBody">
        <div className="grid gridCols3" style={{ gap: 14 }}>
          <div
            className="panel"
            style={{
              padding: 16,
              background:
                health?.status === "ok"
                  ? "rgba(64, 214, 123, 0.08)"
                  : "rgba(255, 183, 64, 0.08)",
              border: `1px solid ${
                health?.status === "ok"
                  ? "rgba(64, 214, 123, 0.25)"
                  : "rgba(255, 183, 64, 0.25)"
              }`,
            }}
          >
            <div className="cardLabel">Backend API</div>
            <div className="cardValue" style={{ fontSize: 20 }}>
              <Badge tone={health?.status === "ok" ? "good" : "warn"}>
                {health?.status ?? (loading ? "..." : "unbekannt")}
              </Badge>
            </div>
            <div className="cardHint">/health Endpoint</div>
          </div>

          <div
            className="panel"
            style={{
              padding: 16,
              background: criticalFlags > 0 ? "rgba(228, 111, 93, 0.08)" : "rgba(64, 214, 123, 0.08)",
              border: `1px solid ${
                criticalFlags > 0 ? "rgba(228, 111, 93, 0.25)" : "rgba(64, 214, 123, 0.25)"
              }`,
            }}
          >
            <div className="cardLabel">Kritische Flags</div>
            <div className="cardValue" style={{ fontSize: 20 }}>
              <Link href="/ops?severity=critical">
                <Badge tone={criticalFlags > 0 ? "bad" : "good"}>
                  {loading ? "..." : criticalFlags}
                </Badge>
              </Link>
            </div>
            <div className="cardHint">Sofortige Aufmerksamkeit erforderlich</div>
          </div>

          <div
            className="panel"
            style={{
              padding: 16,
              background: openFlags > 0 ? "rgba(255, 183, 64, 0.08)" : "rgba(64, 214, 123, 0.08)",
              border: `1px solid ${
                openFlags > 0 ? "rgba(255, 183, 64, 0.25)" : "rgba(64, 214, 123, 0.25)"
              }`,
            }}
          >
            <div className="cardLabel">Offene Flags</div>
            <div className="cardValue" style={{ fontSize: 20 }}>
              <Link href="/ops?severity=all">
                <Badge tone={openFlags > 0 ? "warn" : "good"}>
                  {loading ? "..." : openFlags}
                </Badge>
              </Link>
            </div>
            <div className="cardHint">Ausstehende Datenqualitaetsprobleme</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MarketSection({
  market,
  loading,
}: {
  market: MarketSnapshot | null;
  loading: boolean;
}) {
  const fx = market?.["FX:USD_EUR"] ?? null;

  return (
    <div className="panel" style={{ marginBottom: 18 }}>
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Markt-Snapshot</div>
          <div className="muted small">Aktuelle Marktdaten und Wechselkurse</div>
        </div>
        <Link className="link small" href="/news">
          Marktradar
        </Link>
      </div>
      <div className="panelBody">
        <div className="grid gridCols2" style={{ gap: 14 }}>
          <MarketPriceWidget />
          <KpiCard
            label="USD/EUR Wechselkurs"
            value={fx ? fx.value.toFixed(4) : loading ? "..." : "-"}
            hint={fx ? `Stand: ${fmtDate(fx.observed_at)}` : "FX Feed nicht verfuegbar"}
          />
        </div>
      </div>
    </div>
  );
}

function EntityKPIsSection({
  coopsTotal,
  roastersTotal,
  loading,
}: {
  coopsTotal: number | null;
  roastersTotal: number | null;
  loading: boolean;
}) {
  return (
    <div className="panel" style={{ marginBottom: 18 }}>
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Kooperativen & Roestereien</div>
          <div className="muted small">Inventar und CRM-Pipeline</div>
        </div>
      </div>
      <div className="panelBody">
        <div className="grid gridCols2" style={{ gap: 14 }}>
          <Link href="/cooperatives" style={{ textDecoration: "none" }}>
            <div
              className="panel"
              style={{
                padding: 18,
                background: "rgba(74, 163, 161, 0.08)",
                border: "1px solid rgba(74, 163, 161, 0.25)",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
            >
              <div className="cardLabel">Kooperativen</div>
              <div className="cardValue">{coopsTotal ?? (loading ? "..." : "-")}</div>
              <div className="cardHint">Im System erfasst</div>
            </div>
          </Link>
          <Link href="/roasters" style={{ textDecoration: "none" }}>
            <div
              className="panel"
              style={{
                padding: 18,
                background: "rgba(215, 168, 110, 0.08)",
                border: "1px solid rgba(215, 168, 110, 0.25)",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
            >
              <div className="cardLabel">Roestereien</div>
              <div className="cardValue">{roastersTotal ?? (loading ? "..." : "-")}</div>
              <div className="cardHint">CRM-Pipeline</div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}

function NewsSection({ news, loading }: { news: NewsItem[]; loading: boolean }) {
  return (
    <div className="panel">
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Marktradar</div>
          <div className="muted small">Neueste Headlines (Default: Peru Coffee)</div>
        </div>
        <Link className="link small" href="/news">
          Alle anzeigen
        </Link>
      </div>
      <div className="panelBody">
        {loading ? (
          <div className="muted" style={{ padding: 12 }}>
            Laedt...
          </div>
        ) : news.length === 0 ? (
          <div className="empty">
            Noch keine News. In Ops - &quot;News refresh&quot; starten.
          </div>
        ) : (
          <div className="list">
            {news.slice(0, 5).map((n) => (
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
                    <span>{n.source ?? "-"}</span>
                    <span className="dot">|</span>
                    <span>{fmtDateShort(n.published_at)}</span>
                  </div>
                </div>
                <Badge tone="neutral">{n.topic}</Badge>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ReportsSection({ reports, loading }: { reports: Report[]; loading: boolean }) {
  return (
    <div className="panel">
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Reports & Runs</div>
          <div className="muted small">Letzte Ingest-/Job-Reports</div>
        </div>
        <Link className="link small" href="/reports">
          Alle anzeigen
        </Link>
      </div>
      <div className="panelBody">
        {loading ? (
          <div className="muted" style={{ padding: 12 }}>
            Laedt...
          </div>
        ) : reports.length === 0 ? (
          <div className="empty">Noch keine Reports.</div>
        ) : (
          <div className="list">
            {reports.slice(0, 5).map((r) => (
              <div key={r.id} className="listRow">
                <div className="listMain">
                  <div className="listTitle">
                    <Link href={`/reports/${r.id}`} className="link">
                      {r.name}
                    </Link>
                  </div>
                  <div className="listMeta">
                    <span>{r.kind}</span>
                    <span className="dot">|</span>
                    <span>{fmtDateShort(r.report_at)}</span>
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
          </div>
        )}
      </div>
    </div>
  );
}

function QuickActionsSection() {
  return (
    <div className="panel" style={{ marginTop: 18 }}>
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Quick Links</div>
          <div className="muted small">Schnellzugriff auf wichtige Bereiche</div>
        </div>
      </div>
      <div className="panelBody">
        <div className="chips">
          <Link className="chip" href="/cooperatives">
            Kooperativen
          </Link>
          <Link className="chip" href="/roasters">
            Roestereien
          </Link>
          <Link className="chip" href="/shipments">
            Sendungen
          </Link>
          <Link className="chip" href="/deals">
            Deals
          </Link>
          <Link className="chip" href="/ops">
            Jobs / Ops
          </Link>
          <Link className="chip" href="/alerts">
            Warnungen
          </Link>
          <a className="chip" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            API Docs
          </a>
        </div>
      </div>
    </div>
  );
}

function GettingStartedSection() {
  return (
    <div className="panel" style={{ marginTop: 18 }}>
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Erste Schritte</div>
          <div className="muted small">Empfohlene Aktionen fuer neue Benutzer</div>
        </div>
      </div>
      <div className="panelBody">
        <ol className="steps">
          <li>
            <b>Discovery Seed</b> ausfuehren (Ops) - Kooperativen/Roester initial fuellen.
          </li>
          <li>
            <b>Enrichment</b> aktivieren - Webseiten/Infos ziehen - Scoring.
          </li>
          <li>
            <b>CRM</b> nutzen: Roasters - Outreach - Deals.
          </li>
        </ol>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

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

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setErr(null);

        const [h, m, coops, roasters, n, r, ops] = await Promise.all([
          apiFetch<ApiStatus>("/health", { skipAuth: true }),
          apiFetch<MarketSnapshot>("/market/latest"),
          apiFetch<Paged<any> | any[]>("/cooperatives?limit=1"),
          apiFetch<Paged<any> | any[]>("/roasters?limit=1"),
          apiFetch<NewsItem[]>("/news?limit=6"),
          apiFetch<Report[]>("/reports?limit=6"),
          apiFetch<OpsOverview>("/ops/overview"),
        ]);

        if (!alive) return;
        setHealth(h);
        setMarket(m);
        setCoopsTotal(Array.isArray(coops) ? coops.length : coops?.total ?? null);
        setRoastersTotal(Array.isArray(roasters) ? roasters.length : roasters?.total ?? null);
        setNews(Array.isArray(n) ? n : []);
        setReports(Array.isArray(r) ? r : []);
        setOpsOverview(ops);
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

  return (
    <div className="page">
      {/* Page Header */}
      <div className="pageHeader">
        <div>
          <div className="h1">Uebersicht</div>
          <div className="muted">Executive Operations Dashboard - Status, KPIs und Signale auf einen Blick</div>
        </div>
        <div className="actions">
          <Link className="btn" href="/ops">
            Ops & Jobs
          </Link>
          <button className="btn btnPrimary" onClick={() => window.location.reload()}>
            Aktualisieren
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {err && (
        <ErrorState
          title="Fehler beim Laden der Dashboard-Daten"
          message={err}
          onRetry={() => window.location.reload()}
        />
      )}

      {/* System Health Section */}
      <SystemHealthSection health={health} opsOverview={opsOverview} loading={loading} />

      {/* Market Snapshot */}
      <MarketSection market={market} loading={loading} />

      {/* Entity KPIs */}
      <EntityKPIsSection coopsTotal={coopsTotal} roastersTotal={roastersTotal} loading={loading} />

      {/* News & Reports in 2-column grid */}
      <div className="grid2">
        <NewsSection news={news} loading={loading} />
        <ReportsSection reports={reports} loading={loading} />
      </div>

      {/* Anomaly Feed */}
      <div className="grid2" style={{ marginTop: 18 }}>
        <AnomalyFeedWidget />
        <GettingStartedSection />
      </div>

      {/* Quick Actions */}
      <QuickActionsSection />
    </div>
  );
}
