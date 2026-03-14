"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ErrorPanel } from "../components/AlertError";
import Badge from "../components/Badge";
import { EmptyState, SkeletonKpiGrid, SkeletonRows } from "../components/EmptyState";
import { apiFetch } from "../../lib/api";

type MarktTab = "overview" | "peru" | "signals";

interface LatestSnapshotValue {
  value: number;
  unit?: string | null;
  currency?: string | null;
  observed_at: string;
}

interface LatestSnapshot {
  "FX:USD_EUR": LatestSnapshotValue | null;
  "COFFEE_C:USD_LB": LatestSnapshotValue | null;
  "FREIGHT:USD_PER_40FT": LatestSnapshotValue | null;
}

interface MarketSeriesPoint {
  observed_at: string;
  value: number;
  unit?: string | null;
  currency?: string | null;
}

interface NewsItem {
  id: number;
  topic: string;
  title: string;
  url: string;
  snippet?: string | null;
  country?: string | null;
  published_at?: string | null;
  retrieved_at?: string | null;
}

interface Cooperative {
  id: number;
  name: string;
  region?: string | null;
  certifications?: string | null;
  status: string;
  total_score?: number | null;
  quality_score?: number | null;
  reliability_score?: number | null;
}

interface RealtimeStatus {
  realtime_enabled: boolean;
  cached_price?: {
    price_usd_per_lb?: number;
    observed_at?: string;
    source_name?: string;
  } | null;
  redis_error?: string;
}

const TABS: Array<{ id: MarktTab; label: string }> = [
  { id: "overview", label: "Uebersicht" },
  { id: "peru", label: "Peru Sourcing" },
  { id: "signals", label: "Signale" },
];

function formatTimestamp(value?: string | null) {
  if (!value) return "Keine Daten";
  try {
    return new Date(value).toLocaleString("de-DE");
  } catch {
    return value;
  }
}

function formatShortDate(value?: string | null) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString("de-DE");
  } catch {
    return value;
  }
}

function formatNumber(value?: number | null, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("de-DE", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function certificationsToList(value?: string | null) {
  if (!value) return [];
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function tabTone(change: number) {
  if (change > 0) return "good";
  if (change < 0) return "bad";
  return "neutral";
}

function calculateChange(series: MarketSeriesPoint[]) {
  if (series.length < 2) return null;
  const newest = series[0]?.value;
  const oldest = series[series.length - 1]?.value;
  if (newest === undefined || oldest === undefined || oldest === 0) return null;
  const absolute = newest - oldest;
  const percent = (absolute / oldest) * 100;
  return { absolute, percent };
}

export default function MarktPage() {
  const [activeTab, setActiveTab] = useState<MarktTab>("overview");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastLoadedAt, setLastLoadedAt] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<LatestSnapshot | null>(null);
  const [coffeeSeries, setCoffeeSeries] = useState<MarketSeriesPoint[]>([]);
  const [fxSeries, setFxSeries] = useState<MarketSeriesPoint[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [cooperatives, setCooperatives] = useState<Cooperative[]>([]);
  const [realtime, setRealtime] = useState<RealtimeStatus | null>(null);

  const loadData = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "refresh") {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const [
        latestSnapshot,
        coffeeHistory,
        fxHistory,
        latestNews,
        coopList,
        realtimeStatus,
      ] = await Promise.all([
        apiFetch<LatestSnapshot>("/market/latest"),
        apiFetch<MarketSeriesPoint[]>("/market/series?key=COFFEE_C:USD_LB&limit=30"),
        apiFetch<MarketSeriesPoint[]>("/market/series?key=FX:USD_EUR&limit=30"),
        apiFetch<NewsItem[]>("/news?topic=peru%20coffee&limit=8&days=14"),
        apiFetch<Cooperative[]>("/cooperatives"),
        apiFetch<RealtimeStatus>("/market/realtime/status"),
      ]);

      setSnapshot(latestSnapshot);
      setCoffeeSeries(coffeeHistory);
      setFxSeries(fxHistory);
      setNews(latestNews);
      setCooperatives(coopList);
      setRealtime(realtimeStatus);
      setLastLoadedAt(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Marktdaten konnten nicht geladen werden.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadData("initial");
  }, [loadData]);

  const coffeeChange = useMemo(() => calculateChange(coffeeSeries), [coffeeSeries]);
  const fxChange = useMemo(() => calculateChange(fxSeries), [fxSeries]);

  const topCooperatives = useMemo(() => {
    return [...cooperatives]
      .filter((coop) => coop.total_score !== null && coop.total_score !== undefined)
      .sort((left, right) => (right.total_score ?? 0) - (left.total_score ?? 0))
      .slice(0, 6);
  }, [cooperatives]);

  const regionSummary = useMemo(() => {
    const counts = new Map<string, number>();
    for (const coop of cooperatives) {
      const region = coop.region?.trim() || "Unbekannt";
      counts.set(region, (counts.get(region) ?? 0) + 1);
    }
    return [...counts.entries()]
      .map(([region, count]) => ({ region, count }))
      .sort((left, right) => right.count - left.count)
      .slice(0, 6);
  }, [cooperatives]);

  const certificationSummary = useMemo(() => {
    const counts = new Map<string, number>();
    for (const coop of cooperatives) {
      for (const cert of certificationsToList(coop.certifications)) {
        counts.set(cert, (counts.get(cert) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((left, right) => right.count - left.count)
      .slice(0, 6);
  }, [cooperatives]);

  const healthSignals = useMemo(() => {
    return [
      {
        label: "Arabica zuletzt aktualisiert",
        value: formatTimestamp(snapshot?.["COFFEE_C:USD_LB"]?.observed_at),
        tone: snapshot?.["COFFEE_C:USD_LB"] ? "good" : "warn",
      },
      {
        label: "FX zuletzt aktualisiert",
        value: formatTimestamp(snapshot?.["FX:USD_EUR"]?.observed_at),
        tone: snapshot?.["FX:USD_EUR"] ? "good" : "warn",
      },
      {
        label: "Realtime Feed",
        value: realtime?.realtime_enabled
          ? realtime.cached_price?.source_name || "Aktiv"
          : "Deaktiviert",
        tone: realtime?.realtime_enabled ? "good" : "warn",
      },
      {
        label: "Nachrichtenlage",
        value: news.length > 0 ? `${news.length} Eintraege in 14 Tagen` : "Keine aktuellen Nachrichten",
        tone: news.length > 0 ? "good" : "warn",
      },
    ];
  }, [news.length, realtime, snapshot]);

  return (
    <div className="page">
      <header className="pageHeader">
        <div>
          <h1 className="h1">Kaffee-Marktdaten</h1>
          <p className="muted">
            Operative Marktuebersicht mit Live-Snapshot, Sourcing-Kontext und aktuellen Signalen.
          </p>
        </div>
        <div className="pageActions">
          <span className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
            Stand: {lastLoadedAt ? formatTimestamp(lastLoadedAt) : "Wird geladen"}
          </span>
          <button className="btn btnSecondary" onClick={() => void loadData("refresh")} disabled={refreshing}>
            {refreshing ? "Aktualisiert..." : "Aktualisieren"}
          </button>
        </div>
      </header>

      {error && <ErrorPanel compact message={error} onRetry={() => void loadData("refresh")} />}

      {loading ? (
        <SkeletonKpiGrid count={4} />
      ) : (
        <div className="kpiGrid" style={{ marginBottom: "var(--space-5)" }}>
          <div className="kpiCard">
            <div className="kpiLabel">Arabica</div>
            <div className="kpiValue">
              {formatNumber(snapshot?.["COFFEE_C:USD_LB"]?.value)} {snapshot?.["COFFEE_C:USD_LB"]?.currency || "USD"}
            </div>
            <div className="kpiMeta">
              {coffeeChange ? `${formatNumber(coffeeChange.percent)}% vs. 30er Serie` : "Noch keine Serie"}
            </div>
          </div>

          <div className="kpiCard">
            <div className="kpiLabel">EUR/USD</div>
            <div className="kpiValue">{formatNumber(snapshot?.["FX:USD_EUR"]?.value, 4)}</div>
            <div className="kpiMeta">
              {fxChange ? `${formatNumber(fxChange.percent)}% vs. 30er Serie` : "Noch keine Serie"}
            </div>
          </div>

          <div className="kpiCard">
            <div className="kpiLabel">Frachtindikator</div>
            <div className="kpiValue">{formatNumber(snapshot?.["FREIGHT:USD_PER_40FT"]?.value)}</div>
            <div className="kpiMeta">
              {snapshot?.["FREIGHT:USD_PER_40FT"]?.currency || "USD"} pro 40ft, sofern verfuegbar
            </div>
          </div>

          <div className="kpiCard">
            <div className="kpiLabel">Peru Kooperativen</div>
            <div className="kpiValue">{cooperatives.length}</div>
            <div className="kpiMeta">
              {regionSummary[0] ? `${regionSummary[0].region} ist staerkste Region` : "Noch keine Regionsdaten"}
            </div>
          </div>
        </div>
      )}

      <div
        style={{
          display: "flex",
          gap: "var(--space-2)",
          marginBottom: "var(--space-4)",
          borderBottom: "1px solid var(--color-border)",
          paddingBottom: "var(--space-2)",
          flexWrap: "wrap",
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className="btn"
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: activeTab === tab.id ? "var(--color-primary)" : undefined,
              color: activeTab === tab.id ? "white" : undefined,
            }}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-6)" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            <section className="panel">
              <div className="panelHeader">
                <div className="panelTitle">Marktsnapshot</div>
                <Badge tone="info">Live aus Backend</Badge>
              </div>
              <div className="tableWrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Signal</th>
                      <th style={{ textAlign: "right" }}>Wert</th>
                      <th style={{ textAlign: "right" }}>Trend</th>
                      <th>Letzte Aktualisierung</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Arabica (Coffee C)</td>
                      <td style={{ textAlign: "right" }} className="mono">
                        {formatNumber(snapshot?.["COFFEE_C:USD_LB"]?.value)}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <Badge tone={tabTone(coffeeChange?.percent ?? 0)}>
                          {coffeeChange ? `${formatNumber(coffeeChange.percent)}%` : "—"}
                        </Badge>
                      </td>
                      <td className="muted">{formatTimestamp(snapshot?.["COFFEE_C:USD_LB"]?.observed_at)}</td>
                    </tr>
                    <tr>
                      <td>FX USD/EUR</td>
                      <td style={{ textAlign: "right" }} className="mono">
                        {formatNumber(snapshot?.["FX:USD_EUR"]?.value, 4)}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <Badge tone={tabTone(fxChange?.percent ?? 0)}>
                          {fxChange ? `${formatNumber(fxChange.percent)}%` : "—"}
                        </Badge>
                      </td>
                      <td className="muted">{formatTimestamp(snapshot?.["FX:USD_EUR"]?.observed_at)}</td>
                    </tr>
                    <tr>
                      <td>Fracht 40ft</td>
                      <td style={{ textAlign: "right" }} className="mono">
                        {formatNumber(snapshot?.["FREIGHT:USD_PER_40FT"]?.value)}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <Badge tone={snapshot?.["FREIGHT:USD_PER_40FT"] ? "info" : "warn"}>
                          {snapshot?.["FREIGHT:USD_PER_40FT"] ? "Verfuegbar" : "Fehlt"}
                        </Badge>
                      </td>
                      <td className="muted">{formatTimestamp(snapshot?.["FREIGHT:USD_PER_40FT"]?.observed_at)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <div className="panelHeader">
                <div className="panelTitle">Nachrichtenlage</div>
                <Link href="/news" className="btn btnSecondary">
                  Marktnews
                </Link>
              </div>
              {loading ? (
                <div className="panelBody">
                  <SkeletonRows rows={5} />
                </div>
              ) : news.length === 0 ? (
                <div className="panelBody">
                  <EmptyState title="Keine aktuellen Nachrichten" description="Im aktuellen Zeitraum wurden keine News-Eintraege gefunden." />
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column" }}>
                  {news.map((item, index) => (
                    <a
                      key={item.id}
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        padding: "var(--space-3) var(--space-4)",
                        borderBottom: index < news.length - 1 ? "1px solid var(--color-border)" : "none",
                        textDecoration: "none",
                        color: "inherit",
                      }}
                    >
                      <div style={{ fontWeight: "var(--font-weight-medium)", marginBottom: "var(--space-1)" }}>
                        {item.title}
                      </div>
                      <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                        {item.snippet || "Keine Kurzbeschreibung"} · {formatShortDate(item.published_at || item.retrieved_at)}
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </section>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            <section className="panel">
              <div className="panelHeader">
                <div className="panelTitle">Operative Signale</div>
              </div>
              <div style={{ padding: "var(--space-3)" }}>
                {healthSignals.map((signal) => (
                  <div
                    key={signal.label}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "var(--space-2) 0",
                      borderBottom: "1px solid var(--color-border)",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: "var(--font-weight-medium)" }}>{signal.label}</div>
                      <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                        {signal.value}
                      </div>
                    </div>
                    <Badge tone={signal.tone as "neutral" | "good" | "warn" | "bad" | "info"}>OK</Badge>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panelHeader">
                <div className="panelTitle">Naechste Schritte</div>
              </div>
              <div className="panelBody" style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
                <Link href="/pipeline" className="btn">Pipeline kontrollieren</Link>
                <Link href="/features" className="btn">ML Features pruefen</Link>
                <Link href="/ki" className="btn">KI-Arbeitsbereich oeffnen</Link>
              </div>
            </section>
          </div>
        </div>
      )}

      {activeTab === "peru" && (
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-6)" }}>
          <section className="panel">
            <div className="panelHeader">
              <div className="panelTitle">Top Kooperativen nach Score</div>
              <Link href="/cooperatives" className="btn btnSecondary">
                Alle Kooperativen
              </Link>
            </div>
            {topCooperatives.length === 0 ? (
              <div className="panelBody">
                <EmptyState title="Noch keine bewerteten Kooperativen" description="Sobald Scores vorliegen, erscheinen hier die relevantesten Partner." />
              </div>
            ) : (
              <div className="tableWrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Region</th>
                      <th>Zertifizierungen</th>
                      <th style={{ textAlign: "right" }}>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topCooperatives.map((coop) => (
                      <tr key={coop.id}>
                        <td>
                          <Link href={`/cooperatives/${coop.id}`} className="link">
                            <strong>{coop.name}</strong>
                          </Link>
                        </td>
                        <td className="muted">{coop.region || "—"}</td>
                        <td className="muted">{coop.certifications || "—"}</td>
                        <td style={{ textAlign: "right" }}>
                          <Badge tone="good">{formatNumber(coop.total_score)}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            <section className="panel">
              <div className="panelHeader">
                <div className="panelTitle">Regionen</div>
              </div>
              <div style={{ padding: "var(--space-3)" }}>
                {regionSummary.map((entry) => (
                  <div key={entry.region} style={{ marginBottom: "var(--space-3)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
                      <span>{entry.region}</span>
                      <span className="mono">{entry.count}</span>
                    </div>
                    <div style={{ height: 8, background: "var(--color-bg-muted)", borderRadius: 999 }}>
                      <div
                        style={{
                          width: `${Math.max((entry.count / Math.max(regionSummary[0]?.count || 1, 1)) * 100, 8)}%`,
                          height: "100%",
                          borderRadius: 999,
                          background: "var(--color-primary)",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panelHeader">
                <div className="panelTitle">Zertifizierungen</div>
              </div>
              <div style={{ padding: "var(--space-3)", display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
                {certificationSummary.length === 0 ? (
                  <span className="muted">Keine Zertifizierungen vorhanden</span>
                ) : (
                  certificationSummary.map((entry) => (
                    <Badge key={entry.name} tone="info">
                      {entry.name} · {entry.count}
                    </Badge>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      )}

      {activeTab === "signals" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-6)" }}>
          <section className="panel">
            <div className="panelHeader">
              <div className="panelTitle">Zeitreihenvergleich</div>
            </div>
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Serie</th>
                    <th style={{ textAlign: "right" }}>Neuester Wert</th>
                    <th style={{ textAlign: "right" }}>Aeltester Wert</th>
                    <th style={{ textAlign: "right" }}>Verlauf</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Arabica 30 Eintraege</td>
                    <td style={{ textAlign: "right" }} className="mono">{formatNumber(coffeeSeries[0]?.value)}</td>
                    <td style={{ textAlign: "right" }} className="mono">{formatNumber(coffeeSeries[coffeeSeries.length - 1]?.value)}</td>
                    <td style={{ textAlign: "right" }}>
                      <Badge tone={tabTone(coffeeChange?.percent ?? 0)}>
                        {coffeeChange ? `${formatNumber(coffeeChange.percent)}%` : "—"}
                      </Badge>
                    </td>
                  </tr>
                  <tr>
                    <td>FX 30 Eintraege</td>
                    <td style={{ textAlign: "right" }} className="mono">{formatNumber(fxSeries[0]?.value, 4)}</td>
                    <td style={{ textAlign: "right" }} className="mono">{formatNumber(fxSeries[fxSeries.length - 1]?.value, 4)}</td>
                    <td style={{ textAlign: "right" }}>
                      <Badge tone={tabTone(fxChange?.percent ?? 0)}>
                        {fxChange ? `${formatNumber(fxChange.percent)}%` : "—"}
                      </Badge>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <div className="panelTitle">Realtime und Datenfeed</div>
            </div>
            <div className="panelBody" style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>Realtime Feed</span>
                <Badge tone={realtime?.realtime_enabled ? "good" : "warn"}>
                  {realtime?.realtime_enabled ? "Aktiv" : "Aus"}
                </Badge>
              </div>
              <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                Quelle: {realtime?.cached_price?.source_name || "Keine gecachte Quelle"}
              </div>
              <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                Letzter Tick: {formatTimestamp(realtime?.cached_price?.observed_at)}
              </div>
              {realtime?.redis_error && (
                <Badge tone="warn">Redis Hinweis: {realtime.redis_error}</Badge>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
