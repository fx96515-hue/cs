"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";
import { DataQualityFlag } from "../types";
import { toErrorMessage } from "../utils/error";

type JobResponse = { status: string; task_id: string; report_id: number; message: string };
type EntityType = "cooperative" | "roaster" | "both";
type NewsRefreshResponse = { status: string; created?: number; updated?: number; errors?: unknown[] };

function parseEntityType(value: string): EntityType {
  if (value === "cooperative" || value === "roaster" || value === "both") {
    return value;
  }
  return "both";
}

type OpsOverview = {
  data_quality: {
    freshness_status: string;
    open_flags: number;
    critical_flags: number;
  };
};

function OpsPageContent() {
  const searchParams = useSearchParams();
  const [health, setHealth] = useState<string>("");
  const [topic, setTopic] = useState("peru coffee");
  const [entityType, setEntityType] = useState<EntityType>("both");
  const [max, setMax] = useState(50);
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [overview, setOverview] = useState<OpsOverview | null>(null);
  const [flags, setFlags] = useState<DataQualityFlag[]>([]);
  const [qualityBusy, setQualityBusy] = useState(false);
  const [dqSeverity, setDqSeverity] = useState<string>("all");
  const [dqEntityType, setDqEntityType] = useState<string>("all");
  const [dqIncludeResolved, setDqIncludeResolved] = useState(false);

  const push = useCallback((line: string) => {
    setLog((prev) => [`${new Date().toLocaleTimeString()}  ${line}`, ...prev].slice(0, 120));
  }, []);

  const ping = useCallback(async () => {
    try {
      const d = await apiFetch<{ status: string }>("/health");
      setHealth(d.status);
      push(`health: ${d.status}`);
    } catch (error: unknown) {
      setHealth("down");
      push(`health: ERROR ${toErrorMessage(error)}`);
    }
  }, [push]);

  const loadQuality = useCallback(async () => {
    setQualityBusy(true);
    try {
      const qs = new URLSearchParams();
      qs.set("limit", "50");
      if (dqSeverity !== "all") qs.set("severity", dqSeverity);
      if (dqEntityType !== "all") qs.set("entity_type", dqEntityType);
      if (dqIncludeResolved) qs.set("include_resolved", "true");
      const [o, f] = await Promise.all([
        apiFetch<OpsOverview>("/ops/overview"),
        apiFetch<DataQualityFlag[]>(`/data-quality/flags?${qs.toString()}`),
      ]);
      setOverview(o);
      setFlags(f.slice(0, 12));
    } catch (error: unknown) {
      push(`data-quality: ERROR ${toErrorMessage(error)}`);
    } finally {
      setQualityBusy(false);
    }
  }, [dqEntityType, dqIncludeResolved, dqSeverity, push]);

  useEffect(() => {
    ping();
  }, [ping]);

  useEffect(() => {
    if (!searchParams) return;
    const sev = searchParams.get("severity") ?? "all";
    const ent = searchParams.get("entity_type") ?? "all";
    const inc = searchParams.get("include_resolved") === "true";
    const allowedSev = new Set(["all", "critical", "warning", "info"]);
    const allowedEnt = new Set(["all", "cooperative", "roaster", "lot", "shipment"]);
    setDqSeverity(allowedSev.has(sev) ? sev : "all");
    setDqEntityType(allowedEnt.has(ent) ? ent : "all");
    setDqIncludeResolved(inc);
  }, [searchParams]);

  useEffect(() => {
    loadQuality();
  }, [loadQuality]);

  async function run(name: string, fn: () => Promise<unknown>) {
    setBusy(true);
    try {
      push(`${name}...`);
      const r = await fn();
      push(`${name}: OK ${JSON.stringify(r)}`);
    } catch (error: unknown) {
      push(`${name}: ERROR ${toErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function resolveFlag(id: number) {
    setQualityBusy(true);
    try {
      await apiFetch(`/data-quality/flags/${id}/resolve`, { method: "POST" });
      await loadQuality();
    } catch (error: unknown) {
      push(`resolve-flag: ERROR ${toErrorMessage(error)}`);
    } finally {
      setQualityBusy(false);
    }
  }

  async function recomputeForFlag(flag: DataQualityFlag) {
    setQualityBusy(true);
    try {
      await apiFetch(`/data-quality/recompute/${flag.entity_type}/${flag.entity_id}`, {
        method: "POST",
      });
      await loadQuality();
    } catch (error: unknown) {
      push(`recompute: ERROR ${toErrorMessage(error)}`);
    } finally {
      setQualityBusy(false);
    }
  }

  const criticalFlags = overview?.data_quality?.critical_flags ?? 0;
  const openFlags = overview?.data_quality?.open_flags ?? 0;

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Betrieb</div>
          <div className="muted">One-Click Workflows: Refresh + Discovery + Smoke.</div>
        </div>
        <div className="row gap" style={{ alignItems: "center" }}>
          <Badge tone={health === "ok" ? "good" : health === "" ? "neutral" : "bad"}>
            API: {health}
          </Badge>
          <button className="btn" onClick={ping} disabled={busy}>
            Ping
          </button>
        </div>
      </div>

      <div className="grid2">
        <div className="panel">
          <div className="panelTitle">Aktualisieren</div>
          <div className="muted" style={{ marginBottom: 10 }}>
            Market-FX & Coffee-Price + News-Radar.
          </div>

          <div className="row gap" style={{ flexWrap: "wrap" }}>
            <button
              className="btn btnPrimary"
              disabled={busy}
              onClick={() =>
                run("Market refresh", async () => {
                  return apiFetch<JobResponse>("/market/refresh", { method: "POST" });
                })
              }
            >
              Market-Aktualisierung
            </button>

            <button
              className="btn"
              disabled={busy}
              onClick={() =>
                run("News refresh", async () => {
                  return apiFetch<NewsRefreshResponse>(`/news/refresh?topic=${encodeURIComponent(topic)}`, {
                    method: "POST",
                  });
                })
              }
            >
              News-Aktualisierung
            </button>
          </div>

          <div style={{ marginTop: 14 }}>
            <div className="label">Topic (News)</div>
            <input className="input" value={topic} onChange={(e) => setTopic(e.target.value)} />
          </div>
        </div>

        <div className="panel">
          <div className="panelTitle">Discovery</div>
          <div className="muted" style={{ marginBottom: 10 }}>
            Seeds fuer Kooperativen/Roestereien (Web-Discovery). Laeuft async ueber Celery.
          </div>

          <div className="row gap" style={{ flexWrap: "wrap" }}>
            <div>
              <div className="label">Entitaetstyp</div>
              <select
                className="input"
                value={entityType}
                onChange={(e) => setEntityType(parseEntityType(e.target.value))}
                style={{ width: 220 }}
              >
                <option value="both">beide</option>
                <option value="cooperative">Kooperative</option>
                <option value="roaster">Roesterei</option>
              </select>
            </div>
            <div>
              <div className="label">Max. Entitaeten</div>
              <input
                className="input"
                type="number"
                min={1}
                max={500}
                value={max}
                onChange={(e) => setMax(Number(e.target.value || 50))}
                style={{ width: 160 }}
              />
            </div>
            <div style={{ alignSelf: "end" }}>
              <button
                className="btn btnPrimary"
                disabled={busy}
                onClick={() =>
                  run("Seed discovery", async () => {
                    return apiFetch<JobResponse>("/discovery/seed", {
                      method: "POST",
                      body: JSON.stringify({
                        entity_type: entityType,
                        max_entities: max,
                        dry_run: false,
                      }),
                    });
                  })
                }
              >
                Seed
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 14 }}>
        <div className="panelTitle">Datenqualitaet</div>
        <div className="rowBetween" style={{ marginBottom: 10 }}>
          <div className="muted">Offene Flags und schnelle Korrekturen.</div>
          <div className="row gap">
            <Badge tone={criticalFlags > 0 ? "bad" : "good"}>Critical: {criticalFlags}</Badge>
            <Badge tone="warn">Open: {openFlags}</Badge>
            <button className="btn" onClick={loadQuality} disabled={qualityBusy}>
              Refresh
            </button>
          </div>
        </div>
        <div className="row gap" style={{ marginBottom: 10, flexWrap: "wrap" }}>
          <select
            className="input"
            value={dqSeverity}
            onChange={(e) => setDqSeverity(e.target.value)}
            style={{ width: 160 }}
          >
            <option value="all">Severity: alle</option>
            <option value="critical">critical</option>
            <option value="warning">warning</option>
            <option value="info">info</option>
          </select>
          <select
            className="input"
            value={dqEntityType}
            onChange={(e) => setDqEntityType(e.target.value)}
            style={{ width: 180 }}
          >
            <option value="all">Entity: alle</option>
            <option value="cooperative">cooperative</option>
            <option value="roaster">roaster</option>
            <option value="lot">lot</option>
            <option value="shipment">shipment</option>
          </select>
          <label className="row" style={{ gap: 6 }}>
            <input
              type="checkbox"
              checked={dqIncludeResolved}
              onChange={(e) => setDqIncludeResolved(e.target.checked)}
            />
            <span className="small muted">Resolved anzeigen</span>
          </label>
        </div>

        <div className="tableWrap" style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Entity</th>
                <th>Feld</th>
                <th>Issue</th>
                <th>Severity</th>
                <th>Erkannt</th>
                <th>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {flags.length ? (
                flags.map((flag) => (
                  <tr key={flag.id}>
                    <td className="mono">
                      {flag.entity_type} #{flag.entity_id}
                    </td>
                    <td>{flag.field_name || "-"}</td>
                    <td>{flag.message || flag.issue_type}</td>
                    <td>
                      <Badge
                        tone={
                          flag.severity === "critical"
                            ? "bad"
                            : flag.severity === "warning"
                              ? "warn"
                              : "neutral"
                        }
                      >
                        {flag.severity}
                      </Badge>
                    </td>
                    <td>{new Date(flag.detected_at).toLocaleDateString()}</td>
                    <td>
                      <div className="row" style={{ gap: 8 }}>
                        <button
                          className="btn"
                          onClick={() => recomputeForFlag(flag)}
                          disabled={qualityBusy}
                        >
                          Neu berechnen
                        </button>
                        {flag.resolved_at ? (
                          <span className="muted">Resolved</span>
                        ) : (
                          <button
                            className="btn"
                            onClick={() => resolveFlag(flag.id)}
                            disabled={qualityBusy}
                          >
                            Resolve
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="muted">
                    Keine offenen Flags.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 14 }}>
        <div className="panelTitle">Ausfuehrungsprotokoll</div>
        <div className="codeBox">
          {log.length ? log.map((l, idx) => <div key={idx}>{l}</div>) : <div className="muted">Noch keine Aktionen.</div>}
        </div>
      </div>
    </div>
  );
}

export default function OpsPage() {
  return (
    <Suspense
      fallback={
        <div className="page">
          <div className="pageHeader">
            <div>
              <div className="h1">Betrieb</div>
              <div className="muted">Lade Ansicht...</div>
            </div>
          </div>
          <div className="panel" style={{ padding: 20 }}>
            <div className="muted">Initialisiere Parameter...</div>
          </div>
        </div>
      }
    >
      <OpsPageContent />
    </Suspense>
  );
}
