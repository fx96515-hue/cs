"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { ErrorPanel } from "../components/AlertError";
import Badge from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { ApiError, apiFetch, isDemoMode } from "../../lib/api";

type EntityType = "all" | "cooperative" | "roaster";

interface SearchResult {
  entity_type: "cooperative" | "roaster";
  entity_id: number;
  name: string;
  similarity_score: number;
  region?: string | null;
  city?: string | null;
  certifications?: string | null;
  total_score?: number | null;
}

interface SearchResponse {
  query: string;
  entity_type: EntityType;
  results: SearchResult[];
  total: number;
}

const EXAMPLES = [
  "Bio Kaffee Cajamarca",
  "Roestereien Hamburg",
  "Fair Trade Peru",
  "Single Origin Berlin",
];

function similarityTone(score: number) {
  if (score >= 0.85) return "good";
  if (score >= 0.7) return "info";
  if (score >= 0.5) return "warn";
  return "neutral";
}

function resultHref(result: SearchResult) {
  return result.entity_type === "cooperative"
    ? `/cooperatives/${result.entity_id}`
    : `/roasters/${result.entity_id}`;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [entityType, setEntityType] = useState<EntityType>("all");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [resultTotal, setResultTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [serviceHint, setServiceHint] = useState<string | null>(null);

  async function runSearch(nextQuery?: string) {
    const effectiveQuery = (nextQuery ?? query).trim();
    if (!effectiveQuery || loading) return;

    setLoading(true);
    setSearched(true);
    setError(null);
    setServiceHint(null);

    if (nextQuery) {
      setQuery(nextQuery);
    }

    try {
      const params = new URLSearchParams({
        q: effectiveQuery,
        entity_type: entityType,
        limit: "25",
      });
      const data = await apiFetch<SearchResponse>(`/search/semantic?${params.toString()}`);
      setResults(data.results);
      setResultTotal(data.total);
    } catch (err) {
      setResults([]);
      setResultTotal(0);
      if (err instanceof ApiError && err.status === 503) {
        setServiceHint(err.message);
        return;
      }
      setError(err instanceof Error ? err.message : "Suche konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch();
  }

  const showEmptyResults = searched && !loading && !error && !serviceHint && results.length === 0;

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Semantische Suche</div>
          <div className="muted">
            Durchsucht Kooperativen und Roestereien ueber die semantische Such-API.
          </div>
        </div>
        <div className="pageActions">
          <Badge tone={isDemoMode() ? "warn" : "info"}>
            {isDemoMode() ? "Demo-Modus" : "Live API"}
          </Badge>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: "var(--space-5)" }}>
        <div className="panelHeader">
          <div className="panelTitle">Suchparameter</div>
        </div>
        <div className="panelBody">
          <form className="fieldGrid2" style={{ alignItems: "flex-end" }} onSubmit={handleSubmit}>
            <div className="fieldGroup" style={{ gridColumn: "1 / 3" }}>
              <label className="fieldLabel" htmlFor="semantic-search-query">
                Suchbegriff
              </label>
              <input
                id="semantic-search-query"
                className="input"
                placeholder="z.B. Bio-Kaffee aus Peru oder Roesterei Hamburg"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                disabled={loading}
              />
            </div>

            <div className="fieldGroup">
              <label className="fieldLabel" htmlFor="semantic-search-type">
                Entitaetstyp
              </label>
              <select
                id="semantic-search-type"
                className="input"
                value={entityType}
                onChange={(event) => setEntityType(event.target.value as EntityType)}
                disabled={loading}
              >
                <option value="all">Alle Entitaeten</option>
                <option value="cooperative">Nur Kooperativen</option>
                <option value="roaster">Nur Roestereien</option>
              </select>
            </div>

            <div className="fieldGroup" style={{ display: "flex", alignItems: "flex-end" }}>
              <button className="btn btnPrimary" style={{ width: "100%" }} disabled={!query.trim() || loading} type="submit">
                {loading ? "Suche laeuft..." : "Suchen"}
              </button>
            </div>
          </form>

          {!searched && (
            <div style={{ marginTop: "var(--space-4)", display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
              <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", alignSelf: "center" }}>
                Beispiele:
              </span>
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  className="btn"
                  style={{ fontSize: "var(--font-size-xs)", padding: "4px 10px" }}
                  onClick={() => void runSearch(example)}
                  type="button"
                >
                  {example}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {error && <ErrorPanel compact message={error} onRetry={() => void runSearch()} />}

      {serviceHint && (
        <div className="panel">
          <EmptyState
            title="Semantische Suche derzeit nicht verfuegbar"
            description={serviceHint}
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4" />
                <path d="M12 16h.01" />
              </svg>
            }
          />
        </div>
      )}

      {!searched && !error && !serviceHint && (
        <div className="panel">
          <EmptyState
            title="Suche starten"
            description="Geben Sie einen Begriff ein oder waehlen Sie ein Beispiel. Die Seite nutzt die vorhandene semantische Suchschnittstelle des Backends."
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            }
          />
        </div>
      )}

      {loading && (
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Ergebnisse werden geladen</div>
          </div>
          <div className="panelBody">
            <SkeletonRows rows={5} />
          </div>
        </div>
      )}

      {showEmptyResults && (
        <div className="panel">
          <EmptyState
            title="Keine Treffer"
            description={`Fuer "${query}" wurden in der Such-API keine passenden Eintraege gefunden.`}
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            }
          />
        </div>
      )}

      {results.length > 0 && !loading && (
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">
              {resultTotal} Treffer
              <span className="muted" style={{ fontWeight: "var(--font-weight-normal)", marginLeft: "var(--space-2)" }}>
                fuer &ldquo;{query}&rdquo;
              </span>
            </div>
          </div>
          <div className="tableWrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Typ</th>
                  <th>Region / Stadt</th>
                  <th>Zertifizierungen</th>
                  <th>Aehnlichkeit</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result) => (
                  <tr key={`${result.entity_type}-${result.entity_id}`}>
                    <td>
                      <Link className="link" href={resultHref(result)}>
                        <strong>{result.name}</strong>
                      </Link>
                    </td>
                    <td>
                      <Badge tone={result.entity_type === "cooperative" ? "good" : "info"}>
                        {result.entity_type === "cooperative" ? "Kooperative" : "Roesterei"}
                      </Badge>
                    </td>
                    <td className="muted">{result.region || result.city || "—"}</td>
                    <td className="muted" style={{ maxWidth: 220 }}>
                      {result.certifications || "—"}
                    </td>
                    <td>
                      <Badge tone={similarityTone(result.similarity_score)}>
                        {Math.round(result.similarity_score * 100)}%
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
