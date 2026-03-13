"use client";

import Link from "next/link";
import { useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { ErrorPanel } from "../components/ErrorPanel";
import { useToast } from "../components/ToastProvider";

type SearchResult = {
  entity_type: string;
  entity_id: number;
  name: string;
  similarity_score: number;
  region: string | null;
  city: string | null;
  certifications: string | null;
  total_score: number | null;
};

type SearchResponse = {
  query: string;
  entity_type: string;
  results: SearchResult[];
  total: number;
};

type SimilarEntity = {
  entity_id: number;
  name: string;
  similarity_score: number;
  region: string | null;
  city: string | null;
};

type SimilarResponse = {
  entity_type: string;
  entity_id: number;
  entity_name: string;
  similar_entities: SimilarEntity[];
  total: number;
};

const SEARCH_EXAMPLES = [
  "Bio-Kaffee aus Cajamarca mit Fair Trade",
  "Specialty Röstereien in Hamburg",
  "Kooperativen mit Arabica über 85 Punkte",
  "Nachhaltige Sourcing Partner in Peru",
];

function ScoreBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const tone = pct >= 80 ? "good" : pct >= 60 ? "warn" : "neutral";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
      <div style={{
        width: 56,
        height: 4,
        borderRadius: "var(--radius-full)",
        background: "var(--color-bg-muted)",
        overflow: "hidden",
      }}>
        <div style={{
          width: `${pct}%`,
          height: "100%",
          borderRadius: "var(--radius-full)",
          background: tone === "good"
            ? "var(--color-success)"
            : tone === "warn"
            ? "var(--color-warning)"
            : "var(--color-text-muted)",
        }} />
      </div>
      <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", fontVariantNumeric: "tabular-nums" }}>
        {pct}%
      </span>
    </div>
  );
}

export default function SearchPage() {
  const toast = useToast();
  const [query, setQuery] = useState("");
  const [entityType, setEntityType] = useState<"all" | "cooperative" | "roaster">("all");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [similarMap, setSimilarMap] = useState<Record<string, SimilarEntity[]>>({});
  const [loadingSimilar, setLoadingSimilar] = useState<string | null>(null);

  async function handleSearch(q = query) {
    if (!q.trim()) { toast.warning("Bitte Suchbegriff eingeben"); return; }
    if (isDemoMode()) { toast.info("Semantische Suche ist im Demo-Modus nicht verfügbar."); return; }

    setLoading(true);
    setError(null);
    setResults(null);
    setSimilarMap({});

    try {
      const res = await apiFetch<SearchResponse>(
        `/search/semantic?q=${encodeURIComponent(q)}&entity_type=${entityType}&limit=20`,
      );
      setResults(Array.isArray(res.results) ? res.results : []);
      setQuery(q);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      const friendly = msg.includes("503")
        ? "Semantische Suche nicht verfügbar — OpenAI API-Schlüssel fehlt im Backend."
        : msg;
      setError(friendly);
    } finally {
      setLoading(false);
    }
  }

  async function handleFindSimilar(result: SearchResult) {
    const key = `${result.entity_type}-${result.entity_id}`;
    if (similarMap[key]) return;

    setLoadingSimilar(key);
    try {
      const res = await apiFetch<SimilarResponse>(
        `/search/entity/${result.entity_type}/${result.entity_id}/similar?limit=5`,
      );
      setSimilarMap((prev) => ({ ...prev, [key]: res.similar_entities ?? [] }));
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Fehler beim Laden ähnlicher Entitäten");
    } finally {
      setLoadingSimilar(null);
    }
  }

  function getEntityUrl(type: string, id: number) {
    if (type === "cooperative") return `/cooperatives/${id}`;
    if (type === "roaster") return `/roasters/${id}`;
    return "#";
  }

  const hasResults = results !== null;
  const empty = hasResults && results.length === 0;

  return (
    <div className="page">

      {/* Header */}
      <div className="pageHeader">
        <div>
          <div className="h1">Semantische Suche</div>
          <div className="muted">
            KI-gestützte Vektorsuche über Kooperativen und Röstereien
          </div>
        </div>
        <div className="pageActions">
          <span className="badge badgeInfo" style={{ fontSize: "var(--font-size-xs)", letterSpacing: "0.04em" }}>
            Embedding-Vektoren
          </span>
        </div>
      </div>

      {/* Suchleiste */}
      <div className="panel" style={{ marginBottom: "var(--space-5)" }}>
        <div className="panelHeader">
          <div className="panelTitle">Suchparameter</div>
        </div>
        <div className="panelBody">
          <div className="fieldGrid2" style={{ alignItems: "flex-end" }}>
            <div className="fieldGroup" style={{ gridColumn: "1 / 3" }}>
              <label className="fieldLabel">Suchbegriff</label>
              <div style={{ position: "relative" }}>
                <svg
                  width="15" height="15" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  style={{ position: "absolute", left: "var(--space-3)", top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)", pointerEvents: "none" }}
                >
                  <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                </svg>
                <input
                  className="input"
                  style={{ paddingLeft: "var(--space-8)" }}
                  placeholder="z.B. Bio-Kaffee aus Peru mit Fair Trade Zertifizierung..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
              </div>
            </div>
            <div className="fieldGroup">
              <label className="fieldLabel">Entitätstyp</label>
              <select
                className="input"
                value={entityType}
                onChange={(e) => setEntityType(e.target.value as typeof entityType)}
              >
                <option value="all">Alle Entitäten</option>
                <option value="cooperative">Nur Kooperativen</option>
                <option value="roaster">Nur Röstereien</option>
              </select>
            </div>
            <div className="fieldGroup" style={{ display: "flex", alignItems: "flex-end" }}>
              <button
                className="btn btnPrimary"
                style={{ width: "100%" }}
                onClick={() => handleSearch()}
                disabled={loading || !query.trim()}
              >
                {loading ? (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                      strokeLinecap="round" strokeLinejoin="round"
                      style={{ animation: "spin 1s linear infinite" }}>
                      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                    </svg>
                    Suche...
                  </>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                    </svg>
                    Suchen
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Beispiel-Queries */}
          {!hasResults && (
            <div style={{ marginTop: "var(--space-4)", display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
              <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", alignSelf: "center", marginRight: "var(--space-1)" }}>
                Beispiele:
              </span>
              {SEARCH_EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  className="btn"
                  style={{ fontSize: "var(--font-size-xs)", padding: "4px 10px" }}
                  onClick={() => { setQuery(ex); handleSearch(ex); }}
                  disabled={loading}
                >
                  {ex}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Fehler */}
      {error && <ErrorPanel message={error} onRetry={() => handleSearch()} compact style={{ marginBottom: "var(--space-5)" }} />}

      {/* Leerzustand vor Suche */}
      {!hasResults && !error && !loading && (
        <div className="panel">
          <EmptyState
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
            }
            title="Semantische Suche"
            text="Geben Sie einen Suchbegriff ein oder wählen Sie ein Beispiel. Die KI findet semantisch ähnliche Treffer — auch ohne exakte Schlüsselwörter."
          />
        </div>
      )}

      {/* Keine Treffer */}
      {empty && (
        <div className="panel">
          <EmptyState
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
            }
            title="Keine Treffer"
            text={`Keine Ergebnisse für "${query}". Versuchen Sie andere Begriffe oder wählen Sie einen anderen Entitätstyp.`}
          />
        </div>
      )}

      {/* Ergebnistabelle */}
      {hasResults && results.length > 0 && (
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">
              {results.length} Ergebnis{results.length !== 1 ? "se" : ""}
              <span className="muted" style={{ fontWeight: "var(--font-weight-normal)", marginLeft: "var(--space-2)" }}>
                für &ldquo;{query}&rdquo;
              </span>
            </div>
          </div>
          <div className="tableWrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Typ</th>
                  <th>Region</th>
                  <th>Zertifizierungen</th>
                  <th>Score</th>
                  <th>Relevanz</th>
                  <th style={{ width: 140 }}></th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => {
                  const key = `${r.entity_type}-${r.entity_id}`;
                  const similar = similarMap[key];
                  const isSimilarLoading = loadingSimilar === key;

                  return (
                    <>
                      <tr key={key}>
                        <td>
                          <Link className="link" href={getEntityUrl(r.entity_type, r.entity_id)}>
                            <strong>{r.name}</strong>
                          </Link>
                        </td>
                        <td>
                          <Badge tone={r.entity_type === "cooperative" ? "good" : "neutral"}>
                            {r.entity_type === "cooperative" ? "Kooperative" : "Rösterei"}
                          </Badge>
                        </td>
                        <td className="muted">{r.region || r.city || "—"}</td>
                        <td className="muted" style={{ fontSize: "var(--font-size-xs)", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {r.certifications || "—"}
                        </td>
                        <td>
                          {r.total_score != null
                            ? <Badge tone="neutral">{r.total_score.toFixed(1)}</Badge>
                            : <span className="muted">—</span>
                          }
                        </td>
                        <td>
                          <ScoreBar value={r.similarity_score} />
                        </td>
                        <td>
                          {similar ? (
                            <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)" }}>
                              {similar.length} ähnliche
                            </span>
                          ) : (
                            <button
                              className="btn"
                              style={{ fontSize: "var(--font-size-xs)", padding: "4px 10px" }}
                              onClick={() => handleFindSimilar(r)}
                              disabled={isSimilarLoading}
                            >
                              {isSimilarLoading ? "Lädt..." : "Ähnliche"}
                            </button>
                          )}
                        </td>
                      </tr>

                      {/* Ähnliche Entitäten Inline-Zeile */}
                      {similar && similar.length > 0 && (
                        <tr key={`${key}-similar`} style={{ background: "var(--color-bg-subtle)" }}>
                          <td colSpan={7} style={{ padding: "var(--space-3) var(--space-5)" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap" }}>
                              <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", fontWeight: "var(--font-weight-semibold)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>
                                Ähnlich zu {r.name}
                              </span>
                              {similar.map((s) => (
                                <Link
                                  key={s.entity_id}
                                  href={getEntityUrl(r.entity_type, s.entity_id)}
                                  className="link"
                                  style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    gap: "var(--space-2)",
                                    padding: "4px 10px",
                                    background: "var(--color-surface)",
                                    borderRadius: "var(--radius-full)",
                                    border: "1px solid var(--color-border-strong)",
                                    fontSize: "var(--font-size-xs)",
                                  }}
                                >
                                  {s.name}
                                  <span style={{ color: "var(--color-text-muted)" }}>
                                    {Math.round(s.similarity_score * 100)}%
                                  </span>
                                </Link>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
