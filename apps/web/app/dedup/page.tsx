"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

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
  payload: any;
};

export default function DedupPage() {
  const [entityType, setEntityType] = useState<"cooperative" | "roaster">(
    "cooperative"
  );
  const [suggestions, setSuggestions] = useState<DedupPair[]>([]);
  const [history, setHistory] = useState<MergeHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [threshold, setThreshold] = useState(90);
  const [selectedPair, setSelectedPair] = useState<DedupPair | null>(null);

  async function fetchSuggestions() {
    try {
      setLoading(true);
      const data = await apiFetch<DedupPair[]>(
        `/dedup/suggest?entity_type=${entityType}&threshold=${threshold}&limit=50`
      );
      setSuggestions(data);
    } catch (e) {
      console.error("Failed to fetch suggestions:", e);
    } finally {
      setLoading(false);
    }
  }

  async function fetchHistory() {
    try {
      const data = await apiFetch<MergeHistory[]>(
        `/dedup/history?entity_type=${entityType}&limit=50`
      );
      setHistory(data);
    } catch (e) {
      console.error("Failed to fetch history:", e);
    }
  }

  async function mergePair(keepId: number, mergeId: number) {
    try {
      await apiFetch("/dedup/merge", {
        method: "POST",
        body: JSON.stringify({
          entity_type: entityType,
          keep_id: keepId,
          merge_id: mergeId,
        }),
      });
      alert("Erfolgreich zusammengeführt!");
      setSelectedPair(null);
      fetchSuggestions();
      fetchHistory();
    } catch (e: any) {
      alert(`Fehler beim Zusammenführen: ${e?.message || e}`);
    }
  }

  useEffect(() => {
    fetchSuggestions();
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityType]);

  const scoreColor = (score: number) => {
    if (score >= 95) return "bad";
    if (score >= 90) return "warn";
    return "neutral";
  };

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Duplikate</div>
          <div className="muted">Doppelte Einträge erkennen und zusammenführen</div>
        </div>
      </div>

      <div className="panel">
        <div className="panelTitle">Filter</div>
        <div className="row gap" style={{ flexWrap: "wrap" }}>
          <div>
            <div className="label">Entitätstyp</div>
            <select
              className="input"
              value={entityType}
              onChange={(e) => setEntityType(e.target.value as any)}
            >
              <option value="cooperative">Kooperativen</option>
              <option value="roaster">Röstereien</option>
            </select>
          </div>
          <div>
            <div className="label">Ähnlichkeitsgrenze</div>
            <input
              type="number"
              className="input"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              min={70}
              max={100}
              style={{ width: 100 }}
            />
          </div>
          <div style={{ alignSelf: "end" }}>
            <button className="btn btnPrimary" onClick={fetchSuggestions}>
              Suchen
            </button>
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 14 }}>
        <div className="panelTitle">
          Vorgeschlagene Duplikate ({suggestions.length})
        </div>
        {loading ? (
          <div className="muted">Lädt...</div>
        ) : suggestions.length === 0 ? (
          <div className="muted">Keine Duplikate gefunden.</div>
        ) : (
          <div className="table">
            <table>
              <thead>
                <tr>
                  <th>ID A</th>
                  <th>Name A</th>
                  <th>ID B</th>
                  <th>Name B</th>
                  <th>Ähnlichkeit</th>
                  <th>Grund</th>
                  <th>Aktion</th>
                </tr>
              </thead>
              <tbody>
                {suggestions.map((pair, idx) => (
                  <tr key={idx}>
                    <td>{pair.a_id}</td>
                    <td>{pair.a_name}</td>
                    <td>{pair.b_id}</td>
                    <td>{pair.b_name}</td>
                    <td>
                      <Badge tone={scoreColor(pair.score)}>
                        {pair.score.toFixed(1)}%
                      </Badge>
                    </td>
                    <td>{pair.reason}</td>
                    <td>
                      <button
                        className="btn btnSmall"
                        onClick={() => setSelectedPair(pair)}
                      >
                        Zusammenführen
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedPair && (
        <div className="modal" onClick={() => setSelectedPair(null)}>
          <div className="modalContent" onClick={(e) => e.stopPropagation()}>
            <div className="modalHeader">
              <div className="h2">Zusammenführen bestätigen</div>
              <button
                className="ghost"
                onClick={() => setSelectedPair(null)}
              >
                ×
              </button>
            </div>
            <div className="modalBody">
              <p>
                Welche Entität möchten Sie behalten?
              </p>
              <div className="grid2" style={{ marginTop: 14, gap: 14 }}>
                <div className="panel">
                  <div className="panelTitle">Entität A</div>
                  <div>
                    <strong>ID:</strong> {selectedPair.a_id}
                  </div>
                  <div>
                    <strong>Name:</strong> {selectedPair.a_name}
                  </div>
                  <button
                    className="btn btnPrimary"
                    style={{ marginTop: 10 }}
                    onClick={() =>
                      mergePair(selectedPair.a_id, selectedPair.b_id)
                    }
                  >
                    A behalten, B zusammenführen
                  </button>
                </div>
                <div className="panel">
                  <div className="panelTitle">Entität B</div>
                  <div>
                    <strong>ID:</strong> {selectedPair.b_id}
                  </div>
                  <div>
                    <strong>Name:</strong> {selectedPair.b_name}
                  </div>
                  <button
                    className="btn btnPrimary"
                    style={{ marginTop: 10 }}
                    onClick={() =>
                      mergePair(selectedPair.b_id, selectedPair.a_id)
                    }
                  >
                    B behalten, A zusammenführen
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="panel" style={{ marginTop: 14 }}>
        <div className="panelTitle">Zusammenführungsverlauf ({history.length})</div>
        {history.length === 0 ? (
          <div className="muted">Keine Verlaufsdaten.</div>
        ) : (
          <div className="table">
            <table>
              <thead>
                <tr>
                  <th>Entitäts-ID</th>
                  <th>Datum</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item, idx) => (
                  <tr key={idx}>
                    <td>{item.entity_id}</td>
                    <td>
                      {new Date(item.created_at).toLocaleDateString("de-DE")}
                    </td>
                    <td>
                      <code>{JSON.stringify(item.payload)}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
