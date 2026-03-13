"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { ErrorPanel } from "../components/ErrorPanel";
import { Pagination, usePagination } from "../components/Pagination";
import { useToast } from "../components/ToastProvider";
import { exportToCsv } from "../utils/export";
import { DataQualityFlag } from "../types";
import { toErrorMessage } from "../utils/error";

/* ============================================================
   TYPES
   ============================================================ */

type Coop = {
  id: number;
  name: string;
  region?: string | null;
  region_id?: number | null;
  country?: string | null;
  website?: string | null;
  sca_score?: number | null;
  deleted_at?: string | null;
};

type CoopList = { items: Coop[]; total: number };
type FlagSummary = { count: number; tone: "bad" | "warn" | "neutral" };
type DqFilter = "all" | "any" | "none" | "critical" | "warning" | "info";

const DQ_FILTER_VALUES: DqFilter[] = ["all", "any", "none", "critical", "warning", "info"];
function parseDqFilter(v: string): DqFilter {
  return DQ_FILTER_VALUES.includes(v as DqFilter) ? (v as DqFilter) : "all";
}

/* ============================================================
   ICONS
   ============================================================ */

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="7" cy="7" r="5" /><path d="M12 12L10.5 10.5" />
  </svg>
);
const ExternalIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 3L3 9M9 3H5M9 3v4" />
  </svg>
);
const DownloadIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);

/* ============================================================
   COOPERATIVES PAGE
   ============================================================ */

export default function CooperativesPage() {
  const toast = useToast();
  const [data, setData] = useState<CoopList | null>(null);
  const [flagSummary, setFlagSummary] = useState<Record<number, FlagSummary>>({});
  const [regionMap, setRegionMap] = useState<Record<number, string>>({});
  const [q, setQ] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [dqFilter, setDqFilter] = useState<DqFilter>("all");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setErr(null);
      const [res, flags, regions] = await Promise.all([
        apiFetch<Coop[] | CoopList>(`/cooperatives?limit=500&include_deleted=${showArchived ? "true" : "false"}`),
        apiFetch<DataQualityFlag[]>(`/data-quality/flags?entity_type=cooperative&limit=2000`),
        apiFetch<{ id: number; name: string; country: string }[]>(`/regions?limit=1000`),
      ]);
      setData(Array.isArray(res) ? { items: res, total: res.length } : res);
      const summary: Record<number, FlagSummary> = {};
      for (const flag of flags) {
        const tone = flag.severity === "critical" ? "bad" : flag.severity === "warning" ? "warn" : "neutral";
        const entry = summary[flag.entity_id];
        if (!entry) { summary[flag.entity_id] = { count: 1, tone }; }
        else {
          entry.count += 1;
          if (entry.tone !== "bad" && tone === "bad") entry.tone = "bad";
          if (entry.tone === "neutral" && tone === "warn") entry.tone = "warn";
        }
      }
      setFlagSummary(summary);
      const map: Record<number, string> = {};
      for (const r of regions) map[r.id] = `${r.name} (${r.country})`;
      setRegionMap(map);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [showArchived]);

  useEffect(() => { void load(); }, [load]);

  async function archiveCoop(id: number, name: string) {
    if (!window.confirm(`"${name}" archivieren?`)) return;
    setBusyId(id);
    try {
      await apiFetch(`/cooperatives/${id}`, { method: "DELETE" });
      toast.success(`"${name}" wurde archiviert.`);
      await load();
    } catch (e: unknown) {
      toast.error(toErrorMessage(e));
    } finally { setBusyId(null); }
  }

  async function restoreCoop(id: number, name: string) {
    setBusyId(id);
    try {
      await apiFetch(`/cooperatives/${id}/restore`, { method: "POST" });
      toast.success(`"${name}" wurde wiederhergestellt.`);
      await load();
    } catch (e: unknown) {
      toast.error(toErrorMessage(e));
    } finally { setBusyId(null); }
  }

  function exportCsv() {
    const header = ["ID", "Name", "Region", "Land", "Website", "SCA-Score", "DQ-Flags"].join(";");
    const lines = filtered.map((c) => {
      const region = c.region_id ? regionMap[c.region_id] ?? "" : c.region ?? "";
      return [c.id, c.name, region, c.country ?? "", c.website ?? "", c.sca_score ?? "", flagSummary[c.id]?.count ?? 0].join(";");
    });
    const blob = new Blob([header + "\n" + lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "kooperativen.csv"; a.click();
    URL.revokeObjectURL(url);
    toast.info(`${filtered.length} Einträge exportiert.`);
  }

  const filtered = useMemo(() => {
    const items = data?.items ?? [];
    const qq = q.trim().toLowerCase();
    return items.filter((c) => {
      const regionLabel = c.region_id ? regionMap[c.region_id] ?? "" : c.region ?? "";
      const hay = [c.name, regionLabel, c.country ?? "", c.website ?? ""].join(" ").toLowerCase().includes(qq);
      const summary = flagSummary[c.id];
      const tone = summary?.tone ?? null;
      const passesDq =
        dqFilter === "all" ? true : dqFilter === "any" ? !!summary : dqFilter === "none" ? !summary :
        dqFilter === "critical" ? tone === "bad" : dqFilter === "warning" ? tone === "warn" : tone === "neutral";
      return (!qq || hay) && passesDq;
    });
  }, [data, q, regionMap, flagSummary, dqFilter]);

  const { page, pageSize, setPage, setPageSize, paginated, total } = usePagination(filtered, 25);

  return (
    <div className="content">
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Kooperativen</h1>
          <p className="subtitle">Alles an einem Ort — Suche, Bewertung, Website, Enrichment.</p>
        </div>
        <div className="pageHeaderActions">
          <button className="btn" onClick={exportCsv} disabled={filtered.length === 0}>
            <DownloadIcon /> CSV-Export
          </button>
          <Link href="/ops" className="btn btnPrimary">Enrichment starten</Link>
        </div>
      </header>

      {/* Filters */}
      <div className="panel" style={{ marginBottom: "var(--space-5)" }}>
        <div className="panelBody">
          <div style={{ display: "flex", gap: "var(--space-4)", flexWrap: "wrap", alignItems: "center" }}>
            <div style={{ flex: "1 1 240px", minWidth: 200, position: "relative" }}>
              <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }}>
                <SearchIcon />
              </span>
              <input
                className="input"
                style={{ paddingLeft: 36 }}
                placeholder="Suchen (Name, Region, Website)..."
                value={q}
                onChange={(e) => { setQ(e.target.value); setPage(1); }}
              />
            </div>
            <select
              className="input"
              style={{ width: 160 }}
              value={dqFilter}
              onChange={(e) => { setDqFilter(parseDqFilter(e.target.value)); setPage(1); }}
            >
              <option value="all">DQ: Alle</option>
              <option value="any">DQ: Mit Flags</option>
              <option value="none">DQ: Ohne Flags</option>
              <option value="critical">DQ: Kritisch</option>
              <option value="warning">DQ: Warnung</option>
              <option value="info">DQ: Info</option>
            </select>
            <label style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
                style={{ width: 16, height: 16, accentColor: "var(--color-primary)" }}
              />
              <span className="small muted">Archivierte anzeigen</span>
            </label>
          </div>
        </div>
      </div>

      {err && <ErrorPanel message={err} onRetry={load} />}

      <section className="panel">
        <div className="panelHeader">
          <span className="panelTitle">
            {loading ? "Laden…" : `${filtered.length} Treffer`}
            {data && !loading && <span className="muted" style={{ fontWeight: "normal" }}> von {data.total} gesamt</span>}
          </span>
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Region</th>
                <th>Land</th>
                <th>Website</th>
                <th>SCA</th>
                <th>DQ</th>
                <th style={{ width: 130 }}>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7}><SkeletonRows count={8} /></td></tr>
              ) : paginated.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <EmptyState
                      title="Keine Kooperativen gefunden"
                      description={q ? `Keine Treffer für "${q}". Suche anpassen oder Filter entfernen.` : "Noch keine Kooperativen vorhanden."}
                    />
                  </td>
                </tr>
              ) : (
                paginated.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <Link className="link" href={`/cooperatives/${c.id}`} style={{ fontWeight: 500 }}>
                        {c.name}
                      </Link>
                      {c.deleted_at && <Badge tone="warn" style={{ marginLeft: "var(--space-2)" }}>archiviert</Badge>}
                    </td>
                    <td className="muted">{c.region_id ? regionMap[c.region_id] ?? "—" : c.region ?? "—"}</td>
                    <td className="muted">{c.country ?? "—"}</td>
                    <td>
                      {c.website ? (
                        <a
                          className="link"
                          href={c.website.startsWith("http") ? c.website : `https://${c.website}`}
                          target="_blank"
                          rel="noreferrer"
                          style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
                        >
                          {c.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                          <ExternalIcon />
                        </a>
                      ) : (
                        <Badge tone="warn">fehlend</Badge>
                      )}
                    </td>
                    <td>
                      {c.sca_score ? <Badge tone="good">{c.sca_score}</Badge> : <Badge>—</Badge>}
                    </td>
                    <td>
                      {flagSummary[c.id] ? (
                        <Badge tone={flagSummary[c.id].tone}>{flagSummary[c.id].count}</Badge>
                      ) : (
                        <Badge>0</Badge>
                      )}
                    </td>
                    <td>
                      {c.deleted_at ? (
                        <button className="btn btnSm" onClick={() => restoreCoop(c.id, c.name)} disabled={busyId === c.id}>
                          Wiederherstellen
                        </button>
                      ) : (
                        <button className="btn btnSm" onClick={() => archiveCoop(c.id, c.name)} disabled={busyId === c.id}>
                          Archivieren
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && filtered.length > 0 && (
          <Pagination total={total} page={page} pageSize={pageSize} onPageChange={setPage} onPageSizeChange={setPageSize} />
        )}
      </section>
    </div>
  );
}
