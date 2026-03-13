"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import KpiCard from "../components/KpiCard";
import Badge from "../components/Badge";
import MarketPriceWidget from "../components/MarketPriceWidget";
import AnomalyFeedWidget from "../components/AnomalyFeedWidget";
import { toErrorMessage } from "../utils/error";

type ApiStatus = { status: string };

type MarketPoint = {
  value: number;
  unit?: string | null;
  currency?: string | null;
  observed_at: string;
};

type MarketSnapshot = Record<string, MarketPoint | null>;

type Paged<T> = { items: T[]; total: number };

type InventoryRow = Record<string, unknown>;

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

function fmtDate(x?: string | null) {
  if (!x) return "-";
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
          apiFetch<Paged<InventoryRow> | InventoryRow[]>("/cooperatives?limit=1"),
          apiFetch<Paged<InventoryRow> | InventoryRow[]>("/roasters?limit=1"),
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
      } catch (error: unknown) {
        if (!alive) return;
        setErr(toErrorMessage(error));
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
      {/* Page Header */}
      <div className="pageHeader">
        <div>
          <h1 className="h1">Uebersicht</h1>
          <p className="muted small">Status, KPIs und die wichtigsten Signale auf einen Blick.</p>
        </div>
        <div className="row">
          <Link className="btn" href="/ops">
            Ops & Jobs
          </Link>
          <button className="btn" onClick={() => window.location.reload()}>
            Neu laden
          </button>
        </div>
      </div>

      {/* Error State */}
      {err && (
        <div className="alert bad">
          <div className="alertTitle">Fehler beim Laden</div>
          <div className="alertText">{err}</div>
        </div>
      )}

      {/* KPI Grid */}
      <div className="gridKpi">
        <KpiCard
          label="Backend"
          value={
            <Badge tone={health?.status === "ok" ? "good" : "warn"}>
              {health?.status ?? (loading ? "..." : "unbekannt")}
            </Badge>
          }
          hint="/health"
        />
        <KpiCard
          label="Kooperativen"
          value={coopsTotal ?? (loading ? "..." : "-")}
          hint="Inventar im System"
        />
        <KpiCard
          label="Roestereien"
          value={roastersTotal ?? (loading ? "..." : "-")}
          hint="CRM-Pipeline"
        />
        <KpiCard
          label="Data Quality"
          value={
            <Link href="/ops?severity=critical">
              <Badge tone={opsOverview?.data_quality?.critical_flags ? "bad" : "good"}>
                C: {opsOverview?.data_quality?.critical_flags ?? (loading ? "..." : "0")}
              </Badge>
            </Link>
          }
          hint="Filter in Ops"
        />
        <MarketPriceWidget />
        <KpiCard
          label="USD/EUR"
          value={fx ? fx.value.toFixed(4) : loading ? "..." : "-"}
          hint={fx ? `Stand: ${fmtDate(fx.observed_at)}` : "FX Feed"}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid2">
        {/* Marktradar */}
        <div className="panel" style={{ padding: "20px" }}>
          <div className="rowBetween" style={{ marginBottom: "16px" }}>
            <div>
              <h3 className="h2" style={{ margin: 0 }}>Marktradar</h3>
              <p className="muted small" style={{ marginTop: "4px" }}>Neueste Headlines (Default: Peru Coffee)</p>
            </div>
            <Link className="link small" href="/news">
              Alle anzeigen
            </Link>
          </div>
          <div className="list">
            {(news ?? []).slice(0, 6).map((n) => (
              <div key={n.id} className="listRow">
                <div className="listMain">
                  {n.url ? (
                    <a className="link listTitle" href={n.url} target="_blank" rel="noreferrer">
                      {n.title}
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
            {(!news || news.length === 0) && !loading && (
              <div className="empty">
                Noch keine News. In Ops - "News refresh" starten.
              </div>
            )}
          </div>
        </div>

        {/* Reports */}
        <div className="panel" style={{ padding: "20px" }}>
          <div className="rowBetween" style={{ marginBottom: "16px" }}>
            <div>
              <h3 className="h2" style={{ margin: 0 }}>Reports & Runs</h3>
              <p className="muted small" style={{ marginTop: "4px" }}>Letzte Ingest-/Job-Reports</p>
            </div>
            <Link className="link small" href="/reports">
              Alle anzeigen
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
            {(!reports || reports.length === 0) && !loading && (
              <div className="empty">
                Noch keine Reports.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Anomaly Feed */}
      <AnomalyFeedWidget />

      {/* Bottom Cards */}
      <div className="grid3" style={{ marginTop: "20px" }}>
        <div className="panel" style={{ padding: "20px" }}>
          <h3 className="h2">Naechste Schritte</h3>
          <ol className="steps">
            <li><b>Discovery Seed</b> ausfuehren (Ops) - Kooperativen/Roester initial fuellen.</li>
            <li><b>Enrichment</b> aktivieren - Webseiten/Infos ziehen - Scoring.</li>
            <li><b>CRM</b> nutzen: Roasters - Outreach - Deals.</li>
          </ol>
        </div>
        <div className="panel" style={{ padding: "20px" }}>
          <h3 className="h2">Quick Links</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <Link className="btn btnFull" href="/cooperatives">
              Kooperativen
            </Link>
            <Link className="btn btnFull" href="/roasters">
              Roestereien
            </Link>
            <Link className="btn btnFull" href="/ops">
              Jobs / Ops
            </Link>
          </div>
        </div>
        <div className="panel" style={{ padding: "20px" }}>
          <h3 className="h2">Info</h3>
          <div className="muted small" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <p style={{ margin: 0 }}>Direkter Zugriff:</p>
            <div className="code">UI: localhost:3000</div>
            <div className="code">API: localhost:8000</div>
          </div>
        </div>
      </div>
    </div>
  );
}
