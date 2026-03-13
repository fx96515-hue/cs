"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import { useToast } from "../components/ToastProvider";
import { toErrorMessage } from "../utils/error";

type EntityType = "cooperative" | "roaster";

type DedupPair = {
  a_id: number;
  b_id: number;
  a_name: string;
  b_name: string;
  score: number;
  reason: string;
};

type MergeHistory = {
  entity_id: number;
  created_at: string;
  payload: unknown;
};

function parseEntityType(value: string): EntityType {
  return value === "roaster" ? "roaster" : "cooperative";
}

export default function DedupPage() {
  const toast = useToast();
  const [entityType, setEntityType] = useState<EntityType>("cooperative");
  const [suggestions, setSuggestions] = useState<DedupPair[]>([]);
  const [history, setHistory] = useState<MergeHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [threshold, setThreshold] = useState(90);
  const [selectedPair, setSelectedPair] = useState<DedupPair | null>(null);
  const [isDemo, setIsDemo] = useState(false);

  const fetchSuggestions = useCallback(async () => {
    if (isDemoMode()) { setIsDemo(true); return; }
    try {
      setLoading(true);
      const data = await apiFetch<DedupPair[]>(
        `/dedup/suggest?entity_type=${entityType}&threshold=${threshold}&limit=50`,
      );
      setSuggestions(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Fehler beim Laden der Duplikatvorschläge:", e);
    } finally {
      setLoading(false);
    }
  }, [entityType, threshold]);

  const fetchHistory = useCallback(async () => {
    if (isDemoMode()) return;
    try {
      const data = await apiFetch<MergeHistory[]>(
        `/dedup/history?entity_type=${entityType}&limit=50`,
      );
      setHistory(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Fehler beim Laden des Zusammenführungsverlaufs:", e);
    }
  }, [entityType]);

  async function mergePair(keepId: number, mergeId: number) {
    if (isDemoMode()) return;
    try {
      await apiFetch("/dedup/merge", {
        method: "POST",
        body: JSON.stringify({ entity_type: entityType, keep_id: keepId, merge_id: mergeId }),
      });
      toast.success("Erfolgreich zusammengeführt!");
      setSelectedPair(null);
      void fetchSuggestions();
      void fetchHistory();
    } catch (error: unknown) {
      toast.error(`Fehler beim Zusammenführen: ${toErrorMessage(error)}`);
    }
  }

  useEffect(() => {
    setIsDemo(isDemoMode());
    void fetchSuggestions();
    void fetchHistory();
  }, [fetchHistory, fetchSuggestions]);

  const scoreTone = (score: number): "bad" | "warn" | "neutral" => {
    if (score >= 95) return "bad";
    if (score >= 90) return "warn";
    return "neutral";
  };

  return (
    <>
      {/* Seitenheader */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Duplikatprüfung</h1>
          <p className="subtitle">Doppelte Einträge erkennen und zusammenführen</p>
        </div>
        <div className="pageHeaderActions">
          <button className="btn btnPrimary" onClick={fetchSuggestions} disabled={loading || isDemo}>
            Suche starten
          </button>
        </div>
      </header>

      {/* Filter */}
      <section className="panel" aria-labelledby="filter-title">
        <div className="panelHeader">
          <h2 id="filter-title" className="panelTitle">Suchparameter</h2>
        </div>
        <div className="panelBody">
          <div className="fieldGrid2">
            <div className="field">
              <label className="fieldLabel" htmlFor="entity-type-select">Entitätstyp</label>
              <select
                id="entity-type-select"
                className="input"
                value={entityType}
                onChange={(e) => setEntityType(parseEntityType(e.target.value))}
              >
                <option value="cooperative">Kooperativen</option>
                <option value="roaster">Röstereien</option>
              </select>
            </div>
            <div className="field">
              <label className="fieldLabel" htmlFor="threshold-input">Ähnlichkeitsgrenze (%)</label>
              <input
                id="threshold-input"
                type="number"
                className="input"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                min={70}
                max={100}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Vorschläge */}
      <section className="panel" aria-labelledby="suggestions-title">
        <div className="panelHeader">
          <h2 id="suggestions-title" className="panelTitle">Duplikatvorschläge</h2>
          <span className="badge neutral">{suggestions.length} Treffer</span>
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Eintrag A</th>
                <th>Eintrag B</th>
                <th>Ähnlichkeit</th>
                <th>Begründung</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {isDemo ? (
                <tr><td colSpan={5} className="tableEmpty">Demo-Modus – keine Daten verfügbar.</td></tr>
              ) : loading ? (
                <tr><td colSpan={5} className="tableEmpty">Lädt...</td></tr>
              ) : suggestions.length === 0 ? (
                <tr><td colSpan={5} className="tableEmpty">Keine Duplikate gefunden.</td></tr>
              ) : (
                suggestions.map((pair, idx) => (
                  <tr key={idx}>
                    <td>
                      <div className="strong">#{pair.a_id}</div>
                      <div className="small muted">{pair.a_name}</div>
                    </td>
                    <td>
                      <div className="strong">#{pair.b_id}</div>
                      <div className="small muted">{pair.b_name}</div>
                    </td>
                    <td>
                      <Badge tone={scoreTone(pair.score)}>{pair.score.toFixed(1)} %</Badge>
                    </td>
                    <td className="small">{pair.reason}</td>
                    <td>
                      <button className="btn btnSm" onClick={() => setSelectedPair(pair)}>
                        Zusammenführen
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Zusammenführungsverlauf */}
      <section className="panel" aria-labelledby="history-title">
        <div className="panelHeader">
          <h2 id="history-title" className="panelTitle">Zusammenführungsverlauf</h2>
          <span className="badge neutral">{history.length} Einträge</span>
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Entitäts-ID</th>
                <th>Datum</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {isDemo ? (
                <tr><td colSpan={3} className="tableEmpty">Demo-Modus – keine Daten verfügbar.</td></tr>
              ) : history.length === 0 ? (
                <tr><td colSpan={3} className="tableEmpty">Noch keine Zusammenführungen durchgeführt.</td></tr>
              ) : (
                history.map((item, idx) => (
                  <tr key={idx}>
                    <td><span className="mono">#{item.entity_id}</span></td>
                    <td>{new Date(item.created_at).toLocaleDateString("de-DE")}</td>
                    <td><code className="mono small">{JSON.stringify(item.payload)}</code></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Zusammenführungs-Modal */}
      {selectedPair && (
        <div
          className="modalOverlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="merge-dialog-title"
          onClick={() => setSelectedPair(null)}
        >
          <div className="modalContent" onClick={(e) => e.stopPropagation()}>
            <div className="panelHeader" style={{ padding: "var(--space-5) var(--space-6)" }}>
              <h2 id="merge-dialog-title" className="panelTitle">Zusammenführen bestätigen</h2>
              <button
                className="btn btnSm btnGhost"
                onClick={() => setSelectedPair(null)}
                aria-label="Schließen"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div className="panelBody">
              <p className="subtitle" style={{ marginBottom: "var(--space-5)" }}>
                Welchen Eintrag möchten Sie behalten? Der andere wird zusammengeführt und entfernt.
              </p>
              <div className="grid2col">
                <div className="panel" style={{ background: "var(--color-bg-subtle)" }}>
                  <div className="panelHeader">
                    <h3 className="panelTitle">Eintrag A</h3>
                    <Badge tone="neutral">#{selectedPair.a_id}</Badge>
                  </div>
                  <div className="panelBody">
                    <p className="strong" style={{ marginBottom: "var(--space-4)" }}>{selectedPair.a_name}</p>
                    <button
                      className="btn btnPrimary"
                      onClick={() => mergePair(selectedPair.a_id, selectedPair.b_id)}
                    >
                      A behalten, B zusammenführen
                    </button>
                  </div>
                </div>
                <div className="panel" style={{ background: "var(--color-bg-subtle)" }}>
                  <div className="panelHeader">
                    <h3 className="panelTitle">Eintrag B</h3>
                    <Badge tone="neutral">#{selectedPair.b_id}</Badge>
                  </div>
                  <div className="panelBody">
                    <p className="strong" style={{ marginBottom: "var(--space-4)" }}>{selectedPair.b_name}</p>
                    <button
                      className="btn btnPrimary"
                      onClick={() => mergePair(selectedPair.b_id, selectedPair.a_id)}
                    >
                      B behalten, A zusammenführen
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
