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
      <div className="content">
        {/* Page Header */}
        <div className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Betrieb</h1>
            <p className="subtitle">Systemverwaltung, Workflows und Datenqualitaet</p>
          </div>
          <div className="pageHeaderActions">
            <Badge tone={health === "ok" ? "good" : health === "" ? "neutral" : "bad"}>
              API: {health || "..."}
            </Badge>
            <button className="btn" onClick={ping} disabled={busy}>
              Ping
            </button>
          </div>
        </div>

        {/* KPI Overview */}
        <div className="kpiGrid">
          <div className="kpiCard">
            <span className="cardLabel">API Status</span>
            <span className="cardValue">{health === "ok" ? "Online" : health === "" ? "-" : "Offline"}</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Kritische Flags</span>
            <span className="cardValue">{criticalFlags}</span>
            {criticalFlags > 0 && <span className="cardHint" style={{ color: "var(--color-danger)" }}>Aktion erforderlich</span>}
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Offene Flags</span>
            <span className="cardValue">{openFlags}</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Daten-Aktualitaet</span>
            <span className="cardValue">{overview?.data_quality?.freshness_status || "-"}</span>
          </div>
        </div>

        {/* Actions Grid */}
        <div className="grid2col">
          {/* Refresh Panel */}
          <div className="panel">
            <div className="panelHeader">
              <span className="panelTitle">Aktualisieren</span>
            </div>
            <div className="panelBody">
              <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
                Market-FX, Coffee-Preise und News-Radar aktualisieren.
              </p>
              
              <div className="fieldStack">
                <div className="field">
                  <label className="fieldLabel">Topic (News)</label>
                  <input 
                    className="input" 
                    value={topic} 
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="z.B. peru coffee"
                  />
                </div>
              </div>

              <div className="btnGroup">
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
            </div>
          </div>

          {/* Discovery Panel */}
          <div className="panel">
            <div className="panelHeader">
              <span className="panelTitle">Discovery</span>
            </div>
            <div className="panelBody">
              <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
                Seeds fuer Kooperativen und Roestereien via Web-Discovery.
              </p>
              
              <div className="fieldGrid2">
                <div className="field">
                  <label className="fieldLabel">Entitaetstyp</label>
                  <select
                    className="input"
                    value={entityType}
                    onChange={(e) => setEntityType(parseEntityType(e.target.value))}
                  >
                    <option value="both">Beide</option>
                    <option value="cooperative">Kooperative</option>
                    <option value="roaster">Roesterei</option>
                  </select>
                </div>
                <div className="field">
                  <label className="fieldLabel">Max. Entitaeten</label>
                  <input
                    className="input"
                    type="number"
                    min={1}
                    max={500}
                    value={max}
                    onChange={(e) => setMax(Number(e.target.value || 50))}
                  />
                </div>
              </div>

              <div className="btnGroup">
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
                  Seed starten
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Data Quality Panel */}
        <div className="panel" style={{ marginTop: "var(--space-6)" }}>
          <div className="panelHeader">
            <span className="panelTitle">Datenqualitaet</span>
            <div className="panelActions">
              <Badge tone={criticalFlags > 0 ? "bad" : "good"}>
                Critical: {criticalFlags}
              </Badge>
              <Badge tone="warn">
                Open: {openFlags}
              </Badge>
              <button className="btn btnSm" onClick={loadQuality} disabled={qualityBusy}>
                Aktualisieren
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="panelFilters">
            <select
              className="input"
              value={dqSeverity}
              onChange={(e) => setDqSeverity(e.target.value)}
              style={{ width: "160px" }}
            >
              <option value="all">Severity: Alle</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
            <select
              className="input"
              value={dqEntityType}
              onChange={(e) => setDqEntityType(e.target.value)}
              style={{ width: "180px" }}
            >
              <option value="all">Entity: Alle</option>
              <option value="cooperative">Cooperative</option>
              <option value="roaster">Roaster</option>
              <option value="lot">Lot</option>
              <option value="shipment">Shipment</option>
            </select>
            <label className="checkboxLabel">
              <input
                type="checkbox"
                checked={dqIncludeResolved}
                onChange={(e) => setDqIncludeResolved(e.target.checked)}
              />
              <span>Resolved anzeigen</span>
            </label>
          </div>

          {/* Table */}
          <div className="tableWrap">
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
                      <td>
                        <span className="mono">{flag.entity_type} #{flag.entity_id}</span>
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
                      <td>{new Date(flag.detected_at).toLocaleDateString("de-DE")}</td>
                      <td>
                        <div className="tableActions">
                          <button
                            className="btn btnSm"
                            onClick={() => recomputeForFlag(flag)}
                            disabled={qualityBusy}
                          >
                            Neu berechnen
                          </button>
                          {flag.resolved_at ? (
                            <span className="muted small">Resolved</span>
                          ) : (
                            <button
                              className="btn btnSm"
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
                    <td colSpan={6} className="tableEmpty">
                      Keine offenen Flags vorhanden.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Execution Log */}
        <div className="panel" style={{ marginTop: "var(--space-6)" }}>
          <div className="panelHeader">
            <span className="panelTitle">Ausfuehrungsprotokoll</span>
          </div>
          <div className="panelBody">
            <div className="codeBox">
              {log.length ? (
                log.map((l, idx) => <div key={idx}>{l}</div>)
              ) : (
                <span className="muted">Noch keine Aktionen ausgefuehrt.</span>
              )}
            </div>
          </div>
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
          <div className="content">
            <div className="pageHeader">
              <div className="pageHeaderContent">
                <h1 className="h1">Betrieb</h1>
                <p className="subtitle">Lade Ansicht...</p>
              </div>
            </div>
            <div className="panel">
              <div className="panelBody">
                <span className="muted">Initialisiere Parameter...</span>
              </div>
            </div>
          </div>
        </div>
      }
    >
      <OpsPageContent />
    </Suspense>
  );
}
