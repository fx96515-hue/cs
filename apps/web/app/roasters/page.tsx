"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";
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

/* ============================================================
   ROASTERS PAGE
   ============================================================ */

export default function RoastersPage() {
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
      const [res, flags] = await Promise.all([
        apiFetch<Roaster[] | RoasterList>(
          `/roasters?limit=200&include_deleted=${showArchived ? "true" : "false"}`,
        ),
        apiFetch<DataQualityFlag[]>(`/data-quality/flags?entity_type=roaster&limit=1000`),
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

  useEffect(() => {
    void load();
  }, [load]);

  async function archiveRoaster(id: number) {
    if (!confirm("Rösterei archivieren?")) return;
    setBusyId(id);
    try {
      await apiFetch(`/roasters/${id}`, { method: "DELETE" });
      await load();
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  async function restoreRoaster(id: number) {
    setBusyId(id);
    try {
      await apiFetch(`/roasters/${id}/restore`, { method: "POST" });
      await load();
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  const rows = useMemo(() => {
    const items = data?.items ?? [];
    const qq = q.trim().toLowerCase();
    return items.filter((r) => {
      const hay = [r.name, r.city ?? "", r.country ?? "", r.website ?? ""]
        .join(" ")
        .toLowerCase()
        .includes(qq);

      const summary = flagSummary[r.id];
      const tone = summary?.tone ?? null;
      const passesDq =
        dqFilter === "all" ? true :
        dqFilter === "any" ? !!summary :
        dqFilter === "none" ? !summary :
        dqFilter === "critical" ? tone === "bad" :
        dqFilter === "warning" ? tone === "warn" :
        tone === "neutral";

      return (!qq || hay) && passesDq;
    });
  }, [data, q, flagSummary, dqFilter]);

  return (
    <div className="content">
      {/* Page Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Röstereien</h1>
          <p className="subtitle">CRM-Pipeline, Kontakte und Scoring verwalten.</p>
        </div>
        <div className="pageHeaderActions">
          <Link href="/ops" className="btn">Enrichment starten</Link>
        </div>
      </header>

      {/* Filters */}
      <div className="panel" style={{ marginBottom: "var(--space-5)" }}>
        <div className="panelBody">
          <div className="row" style={{ gap: "var(--space-4)", flexWrap: "wrap" }}>
            <div className="field" style={{ flex: "1 1 240px", minWidth: "200px" }}>
              <div style={{ position: "relative" }}>
                <span style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }}>
                  <SearchIcon />
                </span>
                <input
                  className="input"
                  style={{ paddingLeft: "36px" }}
                  placeholder="Suchen (Name, Stadt, Website)..."
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                />
              </div>
            </div>

            <div className="field" style={{ width: "160px" }}>
              <select
                className="input"
                value={dqFilter}
                onChange={(e) => setDqFilter(parseDqFilter(e.target.value))}
              >
                <option value="all">DQ: Alle</option>
                <option value="any">DQ: Mit Flags</option>
                <option value="none">DQ: Ohne Flags</option>
                <option value="critical">DQ: Kritisch</option>
                <option value="warning">DQ: Warnung</option>
                <option value="info">DQ: Info</option>
              </select>
            </div>

            <label className="row" style={{ gap: "var(--space-2)", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
                style={{ width: "16px", height: "16px", accentColor: "var(--color-primary)" }}
              />
              <span className="small muted">Archivierte anzeigen</span>
            </label>
          </div>
        </div>
      </div>

      {/* Error */}
      {err && (
        <div className="alert bad">
          <div className="alertText">{err}</div>
        </div>
      )}

      {/* Table */}
      <section className="panel">
        <div className="panelHeader">
          <span className="panelTitle">
            {loading ? "Laden..." : `${rows.length} Treffer`}
            {data && !loading && <span className="muted" style={{ fontWeight: "normal" }}> von {data.total} gesamt</span>}
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
                <th style={{ width: "120px" }}>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty">
                      <p className="emptyText">Keine Röstereien gefunden.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                rows.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <Link className="link" href={`/roasters/${r.id}`} style={{ fontWeight: 500 }}>
                        {r.name}
                      </Link>
                      {r.deleted_at && (
                        <Badge tone="warn" style={{ marginLeft: "var(--space-2)" }}>archiviert</Badge>
                      )}
                    </td>
                    <td className="muted">{r.city ?? "-"}</td>
                    <td className="muted">{r.country ?? "-"}</td>
                    <td>
                      {r.website ? (
                        <a
                          className="link row"
                          href={r.website.startsWith("http") ? r.website : `https://${r.website}`}
                          target="_blank"
                          rel="noreferrer"
                          style={{ gap: "var(--space-1)" }}
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
                        <button
                          className="btn btnSm"
                          onClick={() => restoreRoaster(r.id)}
                          disabled={busyId === r.id}
                        >
                          Wiederherstellen
                        </button>
                      ) : (
                        <button
                          className="btn btnSm"
                          onClick={() => archiveRoaster(r.id)}
                          disabled={busyId === r.id}
                        >
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
      </section>
    </div>
  );
}
