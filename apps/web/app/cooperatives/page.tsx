"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";
import { DataQualityFlag } from "../types";
import { toErrorMessage } from "../utils/error";

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

function parseDqFilter(value: string): DqFilter {
  return DQ_FILTER_VALUES.includes(value as DqFilter) ? (value as DqFilter) : "all";
}

export default function CooperativesPage() {
  const [data, setData] = useState<CoopList | null>(null);
  const [flagSummary, setFlagSummary] = useState<Record<number, FlagSummary>>({});
  const [regionMap, setRegionMap] = useState<Record<number, string>>({});
  const [q, setQ] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [dqFilter, setDqFilter] = useState<DqFilter>("all");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [res, flags, regions] = await Promise.all([
        apiFetch<Coop[] | CoopList>(
          `/cooperatives?limit=200&include_deleted=${showArchived ? "true" : "false"}`,
        ),
        apiFetch<DataQualityFlag[]>(`/data-quality/flags?entity_type=cooperative&limit=1000`),
        apiFetch<{ id: number; name: string; country: string }[]>(`/regions?limit=1000`),
      ]);
      if (Array.isArray(res)) {
        setData({ items: res, total: res.length });
      } else {
        setData(res);
      }
      const summary: Record<number, FlagSummary> = {};
      for (const flag of flags) {
        const tone =
          flag.severity === "critical"
            ? "bad"
            : flag.severity === "warning"
              ? "warn"
              : "neutral";
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
      const map: Record<number, string> = {};
      for (const region of regions) {
        map[region.id] = `${region.name} (${region.country})`;
      }
      setRegionMap(map);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    }
  }, [showArchived]);

  useEffect(() => {
    void load();
  }, [load]);

  async function archiveCoop(id: number) {
    if (!confirm("Kooperative archivieren?")) return;
    setBusyId(id);
    try {
      await apiFetch(`/cooperatives/${id}`, { method: "DELETE" });
      await load();
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  async function restoreCoop(id: number) {
    setBusyId(id);
    try {
      await apiFetch(`/cooperatives/${id}/restore`, { method: "POST" });
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
    return items.filter((c) => {
      const regionLabel = c.region_id ? regionMap[c.region_id] ?? "" : c.region ?? "";
      const hay = [c.name, regionLabel, c.country ?? "", c.website ?? ""]
        .join(" ")
        .toLowerCase()
        .includes(qq);

      const summary = flagSummary[c.id];
      const tone = summary?.tone ?? null;
      const passesDq =
        dqFilter === "all"
          ? true
          : dqFilter === "any"
            ? !!summary
            : dqFilter === "none"
              ? !summary
              : dqFilter === "critical"
                ? tone === "bad"
                : dqFilter === "warning"
                  ? tone === "warn"
                  : tone === "neutral";

      return (!qq || hay) && passesDq;
    });
  }, [data, q, regionMap, flagSummary, dqFilter]);

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Kooperativen</div>
          <div className="muted">Alles an einem Ort - Suche, Bewertung, Website, Enrichment.</div>
        </div>
        <div className="row gap">
          <label className="row" style={{ gap: 6 }}>
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            <span className="small muted">Archivierte anzeigen</span>
          </label>
          <input
            className="input"
            placeholder="Suchen (Name, Region, Website)..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className="input"
            value={dqFilter}
            onChange={(e) => setDqFilter(parseDqFilter(e.target.value))}
            style={{ width: 160 }}
          >
            <option value="all">DQ: alle</option>
            <option value="any">DQ: nur mit Flags</option>
            <option value="none">DQ: keine Flags</option>
            <option value="critical">DQ: critical</option>
            <option value="warning">DQ: warning</option>
            <option value="info">DQ: info</option>
          </select>
          <Link className="btn" href="/ops">
            Enrichment starten
          </Link>
        </div>
      </div>

      {err ? <div className="error">{err}</div> : null}

      <div className="panel">
        <div className="panelTitle">
          Treffer: {rows.length} {data ? <span className="muted">(gesamt {data.total})</span> : null}
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
                <th>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link className="link" href={`/cooperatives/${c.id}`}>
                      {c.name}
                    </Link>
                    {c.deleted_at ? (
                      <span style={{ marginLeft: 8 }}>
                        <Badge tone="warn">archiviert</Badge>
                      </span>
                    ) : null}
                  </td>
                  <td className="muted">{c.region_id ? regionMap[c.region_id] ?? "-" : c.region ?? "-"}</td>
                  <td className="muted">{c.country ?? "-"}</td>
                  <td>
                    {c.website ? (
                      <a
                        className="link"
                        href={c.website.startsWith("http") ? c.website : `https://${c.website}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {c.website}
                      </a>
                    ) : (
                      <Badge tone="warn">fehlend</Badge>
                    )}
                  </td>
                  <td>{c.sca_score ? <Badge tone="good">{c.sca_score}</Badge> : <Badge>-</Badge>}</td>
                  <td>
                    {flagSummary[c.id] ? (
                      <Badge tone={flagSummary[c.id].tone}>{flagSummary[c.id].count}</Badge>
                    ) : (
                      <Badge>0</Badge>
                    )}
                  </td>
                  <td>
                    {c.deleted_at ? (
                      <button
                        className="btn"
                        onClick={() => restoreCoop(c.id)}
                        disabled={busyId === c.id}
                      >
                        Restore
                      </button>
                    ) : (
                      <button
                        className="btn"
                        onClick={() => archiveCoop(c.id)}
                        disabled={busyId === c.id}
                      >
                        Archivieren
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
