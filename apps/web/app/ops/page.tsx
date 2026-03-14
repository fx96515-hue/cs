"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import { DataQualityFlag } from "../types";
import { toErrorMessage } from "../utils/error";

type JobResponse = { status: string; task_id: string; report_id?: number; message?: string };
type EntityType = "cooperative" | "roaster" | "both";
type NewsRefreshResponse = { status: string; created?: number; updated?: number; errors?: unknown[] };
type AsyncTaskStatus = {
  task_id: string;
  state?: string;
  ready?: boolean;
  result?: unknown;
  error?: string;
};

function parseEntityType(value: string): EntityType {
  if (value === "cooperative" || value === "roaster" || value === "both") return value;
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
  const [isDemo, setIsDemo] = useState(false);

  const push = useCallback((line: string) => {
    setLog((prev) => [`${new Date().toLocaleTimeString()}  ${line}`, ...prev].slice(0, 150));
  }, []);

  const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const ping = useCallback(async () => {
    if (isDemoMode()) {
      setIsDemo(true);
      setHealth("demo");
      return;
    }
    try {
      const d = await apiFetch<{ status: string }>("/health");
      setHealth(d.status);
      push(`health: ${d.status}`);
    } catch (error: unknown) {
      setHealth("down");
      push(`health: FEHLER ${toErrorMessage(error)}`);
    }
  }, [push]);

  const loadQuality = useCallback(async () => {
    if (isDemoMode()) return;
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
      setFlags(Array.isArray(f) ? f.slice(0, 12) : []);
    } catch (error: unknown) {
      push(`Datenqualitaet: FEHLER ${toErrorMessage(error)}`);
    } finally {
      setQualityBusy(false);
    }
  }, [dqEntityType, dqIncludeResolved, dqSeverity, push]);

  useEffect(() => {
    setIsDemo(isDemoMode());
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

  async function pollTaskStatus(name: string, taskId: string, statusPath: string) {
    const maxPolls = 90;
    for (let attempt = 1; attempt <= maxPolls; attempt++) {
      await wait(2000);
      const status = await apiFetch<AsyncTaskStatus>(`${statusPath}/${taskId}`);
      const state = status.state || (status.ready ? "SUCCESS" : "PENDING");
      if (attempt === 1 || attempt % 5 === 0 || state !== "PENDING") {
        push(`${name}: Status ${state}`);
      }
      if (state === "SUCCESS" || state === "FAILURE" || state === "REVOKED") {
        if (status.result) push(`${name}: Ergebnis ${JSON.stringify(status.result)}`);
        if (status.error) push(`${name}: Fehler ${status.error}`);
        return status;
      }
    }
    push(`${name}: Timeout bei Task-Pruefung`);
    return null;
  }

  async function run(name: string, fn: () => Promise<unknown>, taskStatusPath?: string) {
    if (isDemoMode()) {
      push(`${name}: Demo-Modus - kein Aufruf`);
      return;
    }
    setBusy(true);
    try {
      push(`${name} wird gestartet...`);
      const r = await fn();
      push(`${name}: OK ${JSON.stringify(r)}`);
      const taskId = (r as { task_id?: string } | null | undefined)?.task_id;
      if (taskId && taskStatusPath) {
        push(`${name}: Task ${taskId} in Bearbeitung`);
        await pollTaskStatus(name, taskId, taskStatusPath);
      }
    } catch (error: unknown) {
      push(`${name}: FEHLER ${toErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function resolveFlag(id: number) {
    if (isDemoMode()) return;
    setQualityBusy(true);
    try {
      await apiFetch(`/data-quality/flags/${id}/resolve`, { method: "POST" });
      await loadQuality();
    } catch (error: unknown) {
      push(`Flag aufloesen: FEHLER ${toErrorMessage(error)}`);
    } finally {
      setQualityBusy(false);
    }
  }

  async function recomputeForFlag(flag: DataQualityFlag) {
    if (isDemoMode()) return;
    setQualityBusy(true);
    try {
      await apiFetch(`/data-quality/recompute/${flag.entity_type}/${flag.entity_id}`, { method: "POST" });
      await loadQuality();
    } catch (error: unknown) {
      push(`Neu berechnen: FEHLER ${toErrorMessage(error)}`);
    } finally {
      setQualityBusy(false);
    }
  }

  const criticalFlags = overview?.data_quality?.critical_flags ?? 0;
  const openFlags = overview?.data_quality?.open_flags ?? 0;
  const healthTone = health === "ok" ? "good" : health === "demo" ? "warn" : health === "" ? "neutral" : "bad";
  const healthLabel = health === "ok" ? "Online" : health === "demo" ? "Demo" : health === "" ? "Pruefe..." : "Offline";

  return (
    <>
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Betrieb</h1>
          <p className="subtitle">Systemverwaltung, Workflows und Datenqualitaet</p>
        </div>
        <div className="pageHeaderActions">
          <Badge tone={healthTone}>API: {healthLabel}</Badge>
          <button className="btn" onClick={ping} disabled={busy}>
            Verbindung pruefen
          </button>
        </div>
      </header>

      <div className="kpiGrid">
        <div className="kpiCard">
          <span className="cardLabel">API-Status</span>
          <span className="cardValue">{healthLabel}</span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Kritische Markierungen</span>
          <span className="cardValue" style={{ color: criticalFlags > 0 ? "var(--color-danger)" : undefined }}>
            {isDemo ? "-" : criticalFlags}
          </span>
          {criticalFlags > 0 && <span className="cardHint">Aktion erforderlich</span>}
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Offene Markierungen</span>
          <span className="cardValue">{isDemo ? "-" : openFlags}</span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Datenaktualitaet</span>
          <span className="cardValue">{isDemo ? "-" : (overview?.data_quality?.freshness_status || "-")}</span>
        </div>
      </div>

      <div className="grid2col">
        <section className="panel" aria-labelledby="refresh-title">
          <div className="panelHeader">
            <h2 id="refresh-title" className="panelTitle">Aktualisierung</h2>
          </div>
          <div className="panelBody">
            <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
              Marktdaten, Kaffeepreise und Nachrichtenradar aktualisieren.
            </p>
            <div className="field" style={{ marginBottom: "var(--space-4)" }}>
              <label className="fieldLabel" htmlFor="topic-input">Thema (Nachrichten)</label>
              <input
                id="topic-input"
                className="input"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="z.B. peru coffee"
              />
            </div>
            <div className="btnGroup">
              <button
                className="btn btnPrimary"
                disabled={busy || isDemo}
                onClick={() =>
                  run(
                    "Marktaktualisierung",
                    () => apiFetch<JobResponse>("/market/refresh", { method: "POST" }),
                    "/market/tasks",
                  )
                }
              >
                Marktdaten aktualisieren
              </button>
              <button
                className="btn"
                disabled={busy || isDemo}
                onClick={() =>
                  run(
                    "Nachrichtenaktualisierung",
                    () => apiFetch<NewsRefreshResponse>(`/news/refresh?topic=${encodeURIComponent(topic)}`, { method: "POST" }),
                  )
                }
              >
                Nachrichten aktualisieren
              </button>
            </div>
          </div>
        </section>

        <section className="panel" aria-labelledby="discovery-title">
          <div className="panelHeader">
            <h2 id="discovery-title" className="panelTitle">Ersterfassung</h2>
          </div>
          <div className="panelBody">
            <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
              Kooperativen und Roestereien ueber Web-Suche erstmalig erfassen.
            </p>
            <div className="fieldGrid2">
              <div className="field">
                <label className="fieldLabel" htmlFor="entity-type-select">Entitaetstyp</label>
                <select
                  id="entity-type-select"
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
                <label className="fieldLabel" htmlFor="max-input">Max. Eintraege</label>
                <input
                  id="max-input"
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
                disabled={busy || isDemo}
                onClick={() =>
                  run(
                    "Ersterfassung",
                    () =>
                      apiFetch<JobResponse>("/discovery/seed", {
                        method: "POST",
                        body: JSON.stringify({ entity_type: entityType, max_entities: max, dry_run: false }),
                      }),
                    "/discovery/seed",
                  )
                }
              >
                Ersterfassung starten
              </button>
              <button
                className="btn"
                disabled={busy || isDemo}
                onClick={() =>
                  run("Koop-Datenluecken", () =>
                    apiFetch(`/cooperatives/backfill-missing?limit=${max}`, { method: "POST" }),
                  )
                }
              >
                Fehlende Kooperativen-Daten suchen
              </button>
            </div>
          </div>
        </section>
      </div>

      <section className="panel" aria-labelledby="dq-title">
        <div className="panelHeader">
          <h2 id="dq-title" className="panelTitle">Datenqualitaet</h2>
          <div className="panelActions">
            {!isDemo && (
              <>
                <Badge tone={criticalFlags > 0 ? "bad" : "good"}>Kritisch: {criticalFlags}</Badge>
                <Badge tone={openFlags > 0 ? "warn" : "neutral"}>Offen: {openFlags}</Badge>
              </>
            )}
            <button className="btn btnSm" onClick={loadQuality} disabled={qualityBusy || isDemo}>
              Aktualisieren
            </button>
          </div>
        </div>

        <div className="panelFilters">
          <select className="input" value={dqSeverity} onChange={(e) => setDqSeverity(e.target.value)} style={{ width: 160 }}>
            <option value="all">Schweregrad: Alle</option>
            <option value="critical">Kritisch</option>
            <option value="warning">Warnung</option>
            <option value="info">Info</option>
          </select>
          <select className="input" value={dqEntityType} onChange={(e) => setDqEntityType(e.target.value)} style={{ width: 180 }}>
            <option value="all">Entitaetstyp: Alle</option>
            <option value="cooperative">Kooperative</option>
            <option value="roaster">Roesterei</option>
            <option value="lot">Partie</option>
            <option value="shipment">Sendung</option>
          </select>
          <label className="checkboxLabel">
            <input type="checkbox" checked={dqIncludeResolved} onChange={(e) => setDqIncludeResolved(e.target.checked)} />
            <span>Erledigte einblenden</span>
          </label>
        </div>

        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Entitaet</th>
                <th>Feld</th>
                <th>Problem</th>
                <th>Schweregrad</th>
                <th>Erkannt am</th>
                <th>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {isDemo ? (
                <tr><td colSpan={6} className="tableEmpty">Demo-Modus - keine Daten verfuegbar.</td></tr>
              ) : qualityBusy ? (
                <tr><td colSpan={6} className="tableEmpty">Laedt...</td></tr>
              ) : flags.length > 0 ? (
                flags.map((flag) => (
                  <tr key={flag.id}>
                    <td><span className="mono">{flag.entity_type} #{flag.entity_id}</span></td>
                    <td>{flag.field_name || "-"}</td>
                    <td>{flag.message || flag.issue_type}</td>
                    <td>
                      <Badge tone={flag.severity === "critical" ? "bad" : flag.severity === "warning" ? "warn" : "neutral"}>
                        {flag.severity === "critical" ? "Kritisch" : flag.severity === "warning" ? "Warnung" : "Info"}
                      </Badge>
                    </td>
                    <td>{new Date(flag.detected_at).toLocaleDateString("de-DE")}</td>
                    <td>
                      <div className="tableActions">
                        <button className="btn btnSm" onClick={() => recomputeForFlag(flag)} disabled={qualityBusy}>
                          Neu berechnen
                        </button>
                        {flag.resolved_at ? (
                          <Badge tone="good">Erledigt</Badge>
                        ) : (
                          <button className="btn btnSm" onClick={() => resolveFlag(flag.id)} disabled={qualityBusy}>
                            Erledigen
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={6} className="tableEmpty">Keine offenen Markierungen vorhanden.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel" aria-labelledby="log-title">
        <div className="panelHeader">
          <h2 id="log-title" className="panelTitle">Ausfuehrungsprotokoll</h2>
        </div>
        <div className="panelBody">
          <div className="codeBox">
            {log.length > 0 ? (
              log.map((l, idx) => <div key={idx}>{l}</div>)
            ) : (
              <span className="muted">Noch keine Aktionen ausgefuehrt.</span>
            )}
          </div>
        </div>
      </section>
    </>
  );
}

export default function OpsPage() {
  return (
    <Suspense
      fallback={
        <>
          <header className="pageHeader">
            <div className="pageHeaderContent">
              <h1 className="h1">Betrieb</h1>
              <p className="subtitle">Laedt...</p>
            </div>
          </header>
          <div className="panel">
            <div className="panelBody">
              <span className="muted">Parameter werden initialisiert...</span>
            </div>
          </div>
        </>
      }
    >
      <OpsPageContent />
    </Suspense>
  );
}
