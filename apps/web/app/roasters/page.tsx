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

type Roaster = {
  id: number;
  name: string;
  country?: string | null;
  city?: string | null;
  website?: string | null;
  deleted_at?: string | null;
};

type RoasterList = { items: Roaster[]; total: number };
type FlagSummary = { count: number; tone: "bad" | "warn" | "neutral" };
type DqFilter = "all" | "any" | "none" | "critical" | "warning" | "info";

const DQ_FILTER_VALUES: DqFilter[] = ["all", "any", "none", "critical", "warning", "info"];

function parseDqFilter(value: string): DqFilter {
  return DQ_FILTER_VALUES.includes(value as DqFilter) ? (value as DqFilter) : "all";
}

/* ============================================================
   ICONS
   ============================================================ */

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="7" cy="7" r="5" />
    <path d="M12 12L10.5 10.5" />
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
   ROASTERS PAGE
   ============================================================ */

export default function RoastersPage() {
  const toast = useToast();
  const [data, setData] = useState<RoasterList | null>(null);
  const [flagSummary, setFlagSummary] = useState<Record<number, FlagSummary>>({});
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
      const [res, flags] = await Promise.all([
        apiFetch<Roaster[] | RoasterList>(
          `/roasters?limit=500&include_deleted=${showArchived ? "true" : "false"}`,
        ),
        apiFetch<DataQualityFlag[]>(`/data-quality/flags?entity_type=roaster&limit=2000`),
      ]);
      if (Array.isArray(res)) {
        setData({ items: res, total: res.length });
      } else {
        setData(res);
      }
      const summary: Record<number, FlagSummary> = {};
      for (const flag of flags) {
        const tone =
          flag.severity === "critical" ? "bad" :
          flag.severity === "warning" ? "warn" : "neutral";
        const entry = summary[flag.entity_id];
        if (!entry) {
          summary[flag.entity_id] = { count: 1, tone };
        } else {
          entry.count += 1;
          if (entry.tone !== "bad" && tone === "bad") entry.tone = "bad";
          if (entry.tone === "neutral" && tone === "warn") entry.tone = "warn";
        }
      }
      setFlagSummary(summary);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [showArchived]);

  useEffect(() => { void load(); }, [load]);

  async function archiveRoaster(id: number, name: string) {
    if (!window.confirm(`"${name}" archivieren?`)) return;
    setBusyId(id);
    try {
      await apiFetch(`/roasters/${id}`, { method: "DELETE" });
      toast.success(`"${name}" wurde archiviert.`);
      await load();
    } catch (error: unknown) {
      toast.error(toErrorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  async function restoreRoaster(id: number, name: string) {
    setBusyId(id);
    try {
      await apiFetch(`/roasters/${id}/restore`, { method: "POST" });
      toast.success(`"${name}" wurde wiederhergestellt.`);
      await load();
    } catch (error: unknown) {
      toast.error(toErrorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  // CSV-Export
  function exportCsv() {
    const rows = filtered;
    const header = ["ID", "Name", "Stadt", "Land", "Website", "DQ-Flags"].join(";");
    const lines = rows.map((r) =>
      [r.id, r.name, r.city ?? "", r.country ?? "", r.website ?? "", flagSummary[r.id]?.count ?? 0].join(";")
    );
    const blob = new Blob([header + "\n" + lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "roestereien.csv"; a.click();
    URL.revokeObjectURL(url);
    toast.info(`${rows.length} Einträge exportiert.`);
  }

  const filtered = useMemo(() => {
    const items = data?.items ?? [];
    const qq = q.trim().toLowerCase();
    return items.filter((r) => {
      const hay = [r.name, r.city ?? "", r.country ?? "", r.website ?? ""]
        .join(" ").toLowerCase().includes(qq);
      const summary = flagSummary[r.id];
      const tone = summary?.tone ?? null;
      const passesDq =
        dqFilter === "all" ? true :
        dqFilter === "any" ? !!summary :
        dqFilter === "none" ? !summary :
        dqFilter === "critical" ? tone === "bad" :
        dqFilter === "warning" ? tone === "warn" : tone === "neutral";
      return (!qq || hay) && passesDq;
    });
  }, [data, q, flagSummary, dqFilter]);

  const { page, pageSize, setPage, setPageSize, paginated, total } = usePagination(filtered, 25);

  return (
    <div className="content">
      {/* Page Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Röstereien</h1>
          <p className="subtitle">CRM-Pipeline, Kontakte und Scoring verwalten.</p>
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
                placeholder="Suchen (Name, Stadt, Website)..."
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

      {err && <ErrorPanel message={err} onRetry={fetchRoasters} />}

      {/* Table */}
      <section className="panel">
        <div className="panelHeader">
          <span className="panelTitle">
            {loading ? "Laden…" : `${filtered.length} Treffer`}
            {data && !loading && (
              <span className="muted" style={{ fontWeight: "normal" }}> von {data.total} gesamt</span>
            )}
          </span>
        </div>

        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Stadt</th>
                <th>Land</th>
                <th>Website</th>
                <th>DQ</th>
                <th style={{ width: 130 }}>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6}><SkeletonRows count={8} /></td></tr>
              ) : paginated.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <EmptyState
                      title="Keine Röstereien gefunden"
                      description={q ? `Keine Treffer für "${q}". Suche anpassen oder Filter entfernen.` : "Noch keine Röstereien vorhanden."}
                    />
                  </td>
                </tr>
              ) : (
                paginated.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <Link className="link" href={`/roasters/${r.id}`} style={{ fontWeight: 500 }}>
                        {r.name}
                      </Link>
                      {r.deleted_at && <Badge tone="warn" style={{ marginLeft: "var(--space-2)" }}>archiviert</Badge>}
                    </td>
                    <td className="muted">{r.city ?? "—"}</td>
                    <td className="muted">{r.country ?? "—"}</td>
                    <td>
                      {r.website ? (
                        <a
                          className="link"
                          href={r.website.startsWith("http") ? r.website : `https://${r.website}`}
                          target="_blank"
                          rel="noreferrer"
                          style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
                        >
                          {r.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                          <ExternalIcon />
                        </a>
                      ) : (
                        <Badge tone="warn">fehlend</Badge>
                      )}
                    </td>
                    <td>
                      {flagSummary[r.id] ? (
                        <Badge tone={flagSummary[r.id].tone}>{flagSummary[r.id].count}</Badge>
                      ) : (
                        <Badge>0</Badge>
                      )}
                    </td>
                    <td>
                      {r.deleted_at ? (
                        <button className="btn btnSm" onClick={() => restoreRoaster(r.id, r.name)} disabled={busyId === r.id}>
                          Wiederherstellen
                        </button>
                      ) : (
                        <button className="btn btnSm" onClick={() => archiveRoaster(r.id, r.name)} disabled={busyId === r.id}>
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
          <Pagination
            total={total}
            page={page}
            pageSize={pageSize}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
          />
        )}
      </section>
    </div>
  );
}
