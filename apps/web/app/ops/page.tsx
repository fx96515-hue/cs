"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

type JobResponse = { status: string; task_id?: string; report_id?: number; message?: string };

export default function OpsPage() {
  const [health, setHealth] = useState<string>("?");
  const [topic, setTopic] = useState("peru coffee");
  const [entityType, setEntityType] = useState<"cooperative" | "roaster" | "both">("both");
  const [max, setMax] = useState(50);
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  function push(line: string) {
    setLog((prev) => [`${new Date().toLocaleTimeString()}  ${line}`, ...prev].slice(0, 120));
  }

  async function ping() {
    try {
      const d = await apiFetch<{ status: string }>("/health");
      setHealth(d.status);
      push(`health: ${d.status}`);
    } catch (e: any) {
      setHealth("down");
      push(`health: ERROR ${e?.message ?? e}`);
    }
  }

  useEffect(() => {
    ping();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function run(name: string, fn: () => Promise<any>) {
    setBusy(true);
    try {
      push(`${name}…`);
      const r = await fn();
      push(`${name}: OK ${JSON.stringify(r)}`);
    } catch (e: any) {
      push(`${name}: ERROR ${e?.message ?? e}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Betrieb</div>
          <div className="muted">One-Click Workflows: Refresh + Discovery + Smoke.</div>
        </div>
        <div className="row gap" style={{ alignItems: "center" }}>
          <Badge tone={health === "ok" ? "good" : health === "?" ? "neutral" : "bad"}>API: {health}</Badge>
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
                  // requires backend endpoint /market/refresh (added in this UI release)
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
                  return apiFetch<any>(`/news/refresh?topic=${encodeURIComponent(topic)}`, { method: "POST" });
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
            Seeds für Kooperativen/Röstereien (Web-Discovery). Läuft async über Celery.
          </div>

          <div className="row gap" style={{ flexWrap: "wrap" }}>
            <div>
              <div className="label">Entitätstyp</div>
              <select
                className="input"
                value={entityType}
                onChange={(e) => setEntityType(e.target.value as any)}
                style={{ width: 220 }}
              >
                <option value="both">beide</option>
                <option value="cooperative">Kooperative</option>
                <option value="roaster">Rösterei</option>
              </select>
            </div>
            <div>
              <div className="label">Max. Entitäten</div>
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
                    return apiFetch<any>("/discovery/seed", {
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
        <div className="panelTitle">Ausführungsprotokoll</div>
        <div className="codeBox">
          {log.length ? log.map((l, idx) => <div key={idx}>{l}</div>) : <div className="muted">Noch keine Aktionen.</div>}
        </div>
      </div>
    </div>
  );
}
