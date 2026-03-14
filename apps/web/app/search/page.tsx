"use client";

import Link from "next/link";
import { useState, useMemo } from "react";
import Badge from "../components/Badge";
import { EmptyState } from "../components/EmptyState";

// Demo data for cooperatives and roasters
const COOPERATIVES = [
  { id: 1, name: "Sol y Cafe", type: "cooperative", region: "Cajamarca", city: null, certifications: "Fair Trade, UTZ", score: 89 },
  { id: 2, name: "Cenfrocafe", type: "cooperative", region: "San Martin", city: null, certifications: "Organic, Rainforest Alliance", score: 85 },
  { id: 3, name: "Cooperativa Pangoa", type: "cooperative", region: "Junin", city: null, certifications: "Fair Trade", score: 86 },
  { id: 4, name: "Coopchebi", type: "cooperative", region: "San Martin", city: null, certifications: "Organic", score: 84 },
  { id: 5, name: "Cooperativa La Florida", type: "cooperative", region: "Amazonas", city: null, certifications: "Fair Trade, Organic", score: 88 },
  { id: 6, name: "CAC Alto Mayo", type: "cooperative", region: "San Martin", city: null, certifications: "UTZ, Rainforest Alliance", score: 82 },
  { id: 7, name: "Cooperativa Naranjillo", type: "cooperative", region: "Huanuco", city: null, certifications: "Organic", score: 83 },
  { id: 8, name: "CAC Satipo", type: "cooperative", region: "Junin", city: null, certifications: "Fair Trade", score: 81 },
];

const ROASTERS = [
  { id: 1, name: "Elbgold", type: "roaster", region: null, city: "Hamburg", certifications: "Single Origin, Direct Trade", score: 4.8 },
  { id: 2, name: "The Barn", type: "roaster", region: null, city: "Berlin", certifications: "Single Origin, Peru", score: 4.7 },
  { id: 3, name: "Bonanza Coffee", type: "roaster", region: null, city: "Berlin", certifications: "Peru, Direct Trade", score: 4.6 },
  { id: 4, name: "Man vs Machine", type: "roaster", region: null, city: "Munich", certifications: "Single Origin", score: 4.5 },
  { id: 5, name: "Coffee Circle", type: "roaster", region: null, city: "Berlin", certifications: "Direct Trade, Organic", score: 4.4 },
  { id: 6, name: "Public Coffee Roasters", type: "roaster", region: null, city: "Hamburg", certifications: "Specialty, Peru", score: 4.3 },
  { id: 7, name: "Flying Roasters", type: "roaster", region: null, city: "Berlin", certifications: "Single Origin", score: 4.2 },
  { id: 8, name: "Kaffeekommune", type: "roaster", region: null, city: "Cologne", certifications: "Fair Trade", score: 4.1 },
];

const ALL_ENTITIES = [...COOPERATIVES, ...ROASTERS];

const SEARCH_EXAMPLES = [
  "Bio Kaffee Cajamarca",
  "Roestereien Hamburg",
  "Fair Trade Peru",
  "Single Origin Berlin",
];

function ScoreBar({ value, isRating = false }: { value: number; isRating?: boolean }) {
  const pct = isRating ? Math.round((value / 5) * 100) : value;
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
        {isRating ? value.toFixed(1) : `${pct}%`}
      </span>
    </div>
  );
}

function searchEntities(query: string, entityType: string) {
  const q = query.toLowerCase().trim();
  if (!q) return [];
  
  let entities = ALL_ENTITIES;
  if (entityType === "cooperative") entities = COOPERATIVES;
  if (entityType === "roaster") entities = ROASTERS;
  
  return entities
    .map(entity => {
      let score = 0;
      const searchText = `${entity.name} ${entity.region || ''} ${entity.city || ''} ${entity.certifications || ''}`.toLowerCase();
      
      // Exact match in name gets highest score
      if (entity.name.toLowerCase().includes(q)) score += 50;
      // Region/city match
      if ((entity.region || '').toLowerCase().includes(q)) score += 30;
      if ((entity.city || '').toLowerCase().includes(q)) score += 30;
      // Certification match
      if ((entity.certifications || '').toLowerCase().includes(q)) score += 20;
      // Partial word match
      q.split(' ').forEach(word => {
        if (word.length > 2 && searchText.includes(word)) score += 10;
      });
      
      return { ...entity, relevanceScore: score };
    })
    .filter(e => e.relevanceScore > 0)
    .sort((a, b) => b.relevanceScore - a.relevanceScore);
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [entityType, setEntityType] = useState<"all" | "cooperative" | "roaster">("all");
  const [hasSearched, setHasSearched] = useState(false);

  const results = useMemo(() => {
    if (!hasSearched || !query.trim()) return [];
    return searchEntities(query, entityType);
  }, [query, entityType, hasSearched]);

  function handleSearch(q = query) {
    if (!q.trim()) return;
    setQuery(q);
    setHasSearched(true);
  }

  function getEntityUrl(type: string, id: number) {
    if (type === "cooperative") return `/cooperatives/${id}`;
    if (type === "roaster") return `/roasters/${id}`;
    return "#";
  }

  const empty = hasSearched && results.length === 0;

  return (
    <div className="page">

      {/* Header */}
      <div className="pageHeader">
        <div>
          <div className="h1">Suche</div>
          <div className="muted">
            Durchsuchen Sie Kooperativen und Roestereien
          </div>
        </div>
        <div className="pageActions">
          <span className="badge badgeSuccess" style={{ fontSize: "var(--font-size-xs)" }}>
            Client-Side Suche
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
                  placeholder="z.B. Bio-Kaffee aus Peru, Roesterei Hamburg..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
              </div>
            </div>
            <div className="fieldGroup">
              <label className="fieldLabel">Entitaetstyp</label>
              <select
                className="input"
                value={entityType}
                onChange={(e) => setEntityType(e.target.value as typeof entityType)}
              >
                <option value="all">Alle Entitaeten</option>
                <option value="cooperative">Nur Kooperativen</option>
                <option value="roaster">Nur Roestereien</option>
              </select>
            </div>
            <div className="fieldGroup" style={{ display: "flex", alignItems: "flex-end" }}>
              <button
                className="btn btnPrimary"
                style={{ width: "100%" }}
                onClick={() => handleSearch()}
                disabled={!query.trim()}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                </svg>
                Suchen
              </button>
            </div>
          </div>

          {/* Beispiel-Queries */}
          {!hasSearched && (
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
                >
                  {ex}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Leerzustand vor Suche */}
      {!hasSearched && (
        <div className="panel">
          <EmptyState
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
            }
            title="Suche starten"
            text="Geben Sie einen Suchbegriff ein oder waehlen Sie ein Beispiel. Die Suche findet passende Kooperativen und Roestereien."
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
            text={`Keine Ergebnisse fuer "${query}". Versuchen Sie andere Begriffe oder waehlen Sie einen anderen Entitaetstyp.`}
          />
        </div>
      )}

      {/* Ergebnistabelle */}
      {hasSearched && results.length > 0 && (
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">
              {results.length} Ergebnis{results.length !== 1 ? "se" : ""}
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
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={`${r.type}-${r.id}`}>
                    <td>
                      <Link className="link" href={getEntityUrl(r.type, r.id)}>
                        <strong>{r.name}</strong>
                      </Link>
                    </td>
                    <td>
                      <Badge tone={r.type === "cooperative" ? "good" : "neutral"}>
                        {r.type === "cooperative" ? "Kooperative" : "Roesterei"}
                      </Badge>
                    </td>
                    <td className="muted">{r.region || r.city || "—"}</td>
                    <td className="muted" style={{ fontSize: "var(--font-size-xs)", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {r.certifications || "—"}
                    </td>
                    <td>
                      <ScoreBar value={r.score} isRating={r.type === "roaster"} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Link zum KI-Assistenten */}
      {hasSearched && (
        <div style={{ 
          marginTop: "var(--space-4)", 
          padding: "var(--space-4)", 
          background: "var(--color-bg-subtle)", 
          borderRadius: "var(--radius-lg)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}>
          <div>
            <strong style={{ color: "var(--color-text)" }}>Komplexere Fragen?</strong>
            <span className="muted" style={{ marginLeft: "var(--space-2)" }}>
              Nutzen Sie den KI-Assistenten fuer natuerlichsprachige Anfragen.
            </span>
          </div>
          <Link href="/ki" className="btn btnPrimary">
            KI-Assistent oeffnen
          </Link>
        </div>
      )}
    </div>
  );
}
