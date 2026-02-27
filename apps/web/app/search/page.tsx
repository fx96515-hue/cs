"use client";

import Link from "next/link";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

type SearchResult = {
  entity_type: string;
  entity_id: number;
  name: string;
  similarity_score: number;
  region?: string | null;
  city?: string | null;
  certifications?: string | null;
  total_score?: number | null;
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
  region?: string | null;
  city?: string | null;
  certifications?: string | null;
  total_score?: number | null;
};

type SimilarResponse = {
  entity_type: string;
  entity_id: number;
  entity_name: string;
  similar_entities: SimilarEntity[];
  total: number;
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [entityType, setEntityType] = useState<"all" | "cooperative" | "roaster">("all");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [similarResults, setSimilarResults] = useState<{ [key: string]: SimilarEntity[] }>({});

  const handleSearch = async () => {
    if (!query.trim()) {
      setError("Bitte Suchbegriff eingeben");
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    setSimilarResults({});

    try {
      const response = await apiFetch<SearchResponse>(
        `/search/semantic?q=${encodeURIComponent(query)}&entity_type=${entityType}&limit=20`
      );
      setResults(response.results);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      if (errorMessage.includes("503")) {
        setError("Semantische Suche ist nicht verfügbar. OpenAI API-Schlüssel nicht konfiguriert.");
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFindSimilar = async (result: SearchResult) => {
    const key = `${result.entity_type}-${result.entity_id}`;
    
    try {
      const response = await apiFetch<SimilarResponse>(
        `/search/entity/${result.entity_type}/${result.entity_id}/similar?limit=5`
      );
      setSimilarResults((prev) => ({
        ...prev,
        [key]: response.similar_entities,
      }));
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      setError(errorMessage);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const formatSimilarity = (score: number) => {
    return `${Math.round(score * 100)}%`;
  };

  const getEntityUrl = (entityType: string, entityId: number) => {
    if (entityType === "cooperative") {
      return `/cooperatives/${entityId}`;
    } else if (entityType === "roaster") {
      return `/roasters/${entityId}`;
    }
    return "#";
  };

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Semantische Suche</div>
          <div className="muted">
            KI-gestützte Suche über Kooperativen und Röstereien mit Embedding-Vektoren
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panelTitle">Suchparameter</div>
        <div className="row gap" style={{ alignItems: "flex-end", marginBottom: "1rem" }}>
          <div style={{ flex: 1 }}>
            <label className="label">Suchbegriff</label>
            <input
              className="input"
              placeholder="z.B. 'Bio-Kaffee aus Peru' oder 'Specialty Rösterei Hamburg'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
            />
          </div>
          <div style={{ minWidth: "200px" }}>
            <label className="label">Entitätstyp</label>
            <select
              className="input"
              value={entityType}
              onChange={(e) => setEntityType(e.target.value as "all" | "cooperative" | "roaster")}
            >
              <option value="all">Alle</option>
              <option value="cooperative">Kooperativen</option>
              <option value="roaster">Röstereien</option>
            </select>
          </div>
          <button
            className="btn"
            onClick={handleSearch}
            disabled={loading || !query.trim()}
          >
            {loading ? "Suche..." : "Suchen"}
          </button>
        </div>
      </div>

      {error && (
        <div className="panel" style={{ borderLeft: "4px solid var(--color-error)" }}>
          <div style={{ color: "var(--color-error)" }}>{error}</div>
        </div>
      )}

      {results && (
        <div className="panel">
          <div className="panelTitle">
            Ergebnisse: {results.length}
            {results.length > 0 && (
              <span className="muted" style={{ marginLeft: "0.5rem", fontWeight: "normal" }}>
                für &quot;{query}&quot;
              </span>
            )}
          </div>

          {results.length === 0 ? (
            <div className="muted" style={{ padding: "2rem", textAlign: "center" }}>
              Keine Ergebnisse gefunden. Versuchen Sie andere Suchbegriffe.
            </div>
          ) : (
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Typ</th>
                    <th>Region/Stadt</th>
                    <th>Zertifizierungen</th>
                    <th>Score</th>
                    <th>Ähnlichkeit</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => {
                    const key = `${result.entity_type}-${result.entity_id}`;
                    const similar = similarResults[key];
                    
                    return (
                      <>
                        <tr key={key}>
                          <td>
                            <Link
                              className="link"
                              href={getEntityUrl(result.entity_type, result.entity_id)}
                            >
                              {result.name}
                            </Link>
                          </td>
                          <td>
                            <Badge tone={result.entity_type === "cooperative" ? "good" : "neutral"}>
                              {result.entity_type === "cooperative" ? "Kooperative" : "Rösterei"}
                            </Badge>
                          </td>
                          <td className="muted">
                            {result.region || result.city || "–"}
                          </td>
                          <td className="muted" style={{ fontSize: "0.85rem" }}>
                            {result.certifications || "–"}
                          </td>
                          <td>
                            {result.total_score ? (
                              <Badge tone="neutral">{result.total_score.toFixed(1)}</Badge>
                            ) : (
                              "–"
                            )}
                          </td>
                          <td>
                            <Badge tone="warn">{formatSimilarity(result.similarity_score)}</Badge>
                          </td>
                          <td>
                            <button
                              className="btn btn-sm"
                              onClick={() => handleFindSimilar(result)}
                              disabled={!!similar}
                            >
                              {similar ? "✓ Geladen" : "Ähnliche anzeigen"}
                            </button>
                          </td>
                        </tr>
                        {similar && similar.length > 0 && (
                          <tr key={`${key}-similar`}>
                            <td colSpan={7} style={{ backgroundColor: "var(--color-bg-secondary)", padding: "1rem" }}>
                              <div style={{ marginBottom: "0.5rem", fontWeight: "600" }}>
                                Ähnliche Entitäten zu &quot;{result.name}&quot;:
                              </div>
                              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
                                {similar.map((sim) => (
                                  <Link
                                    key={sim.entity_id}
                                    href={getEntityUrl(result.entity_type, sim.entity_id)}
                                    className="link"
                                    style={{
                                      display: "inline-flex",
                                      alignItems: "center",
                                      gap: "0.5rem",
                                      padding: "0.5rem 0.75rem",
                                      backgroundColor: "var(--color-bg)",
                                      borderRadius: "4px",
                                      border: "1px solid var(--color-border)",
                                    }}
                                  >
                                    <span>{sim.name}</span>
                                    <Badge tone="warn">
                                      {formatSimilarity(sim.similarity_score)}
                                    </Badge>
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
          )}
        </div>
      )}

      {!results && !loading && (
        <div className="panel">
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--color-muted)" }}>
            <div style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>🔍</div>
            <div>Geben Sie einen Suchbegriff ein, um zu beginnen.</div>
            <div style={{ fontSize: "0.9rem", marginTop: "1rem" }}>
              Die semantische Suche nutzt KI-Embeddings, um ähnliche Entitäten zu finden,
              auch wenn die exakten Suchbegriffe nicht übereinstimmen.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
