"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";
import { DataQualityFlag } from "../types";

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

export default function RoastersPage() {
  const [data, setData] = useState<RoasterList | null>(null);
  const [flagSummary, setFlagSummary] = useState<Record<number, FlagSummary>>({});
  const [q, setQ] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [dqFilter, setDqFilter] = useState<"all" | "any" | "none" | "critical" | "warning" | "info">("all");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
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
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  useEffect(() => {
    load();
  }, [showArchived]);

  async function archiveRoaster(id: number) {
    if (!confirm("Roesterei archivieren?")) return;
    setBusyId(id);
    try {
      await apiFetch(`/roasters/${id}`, { method: "DELETE" });
      await load();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setBusyId(null);
    }
  }

  async function restoreRoaster(id: number) {
    setBusyId(id);
    try {
      await apiFetch(`/roasters/${id}/restore`, { method: "POST" });
      await load();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
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
  }, [data, q, flagSummary, dqFilter]);

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Roestereien</div>
          <div className="muted">CRM-Pipeline + Kontakte + Scoring.</div>
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
            placeholder="Suchen (Name, Stadt, Website)..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className="input"
            value={dqFilter}
            onChange={(e) => setDqFilter(e.target.value as any)}
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
                <th>Stadt</th>
                <th>Land</th>
                <th>Website</th>
                <th>DQ</th>
                <th>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link className="link" href={`/roasters/${r.id}`}>
                      {r.name}
                    </Link>
                    {r.deleted_at ? (
                      <span style={{ marginLeft: 8 }}>
                        <Badge tone="warn">archiviert</Badge>
                      </span>
                    ) : null}
                  </td>
                  <td className="muted">{r.city ?? "-"}</td>
                  <td className="muted">{r.country ?? "-"}</td>
                  <td>
                    {r.website ? (
                      <a
                        className="link"
                        href={r.website.startsWith("http") ? r.website : `https://${r.website}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {r.website}
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
                        className="btn"
                        onClick={() => restoreRoaster(r.id)}
                        disabled={busyId === r.id}
                      >
                        Restore
                      </button>
                    ) : (
                      <button
                        className="btn"
                        onClick={() => archiveRoaster(r.id)}
                        disabled={busyId === r.id}
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
