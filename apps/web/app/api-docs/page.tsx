"use client";

import { useState } from "react";

// API documentation and testing page
export default function APIDocsPage() {
  const [response, setResponse] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState("/api/seed-data?type=stats");

  const endpoints = [
    { path: "/api/seed-data?type=stats", description: "Statistik-Uebersicht aller Daten" },
    { path: "/api/seed-data?type=cooperatives", description: "Alle Kooperativen (13 Eintraege)" },
    { path: "/api/seed-data?type=cooperatives&country=PE", description: "Peru Kooperativen (8 Eintraege)" },
    { path: "/api/seed-data?type=cooperatives&country=CO", description: "Kolumbien Kooperativen" },
    { path: "/api/seed-data?type=cooperatives&country=ET", description: "Aethiopien Kooperativen" },
    { path: "/api/seed-data?type=cooperatives&country=BR", description: "Brasilien Kooperativen" },
    { path: "/api/seed-data?type=cooperatives&region=cajamarca", description: "Cajamarca Kooperativen" },
    { path: "/api/seed-data?type=roasters", description: "Deutsche Roestereien (8 Eintraege)" },
    { path: "/api/seed-data?type=regions", description: "Peru Anbauregionen (6 Eintraege)" },
    { path: "/api/seed-data?type=market", description: "Aktuelle Marktdaten" },
    { path: "/api/seed-data?type=all", description: "Alle Daten komplett" },
    { path: "/api/coffee-prices", description: "Kaffeepreise (mit Yahoo Finance Fallback)" },
  ];

  const testEndpoint = async (endpoint: string) => {
    setLoading(true);
    setSelectedEndpoint(endpoint);
    try {
      const res = await fetch(endpoint);
      const data = await res.json();
      setResponse(JSON.stringify(data, null, 2));
    } catch (error) {
      setResponse(`Error: ${error}`);
    }
    setLoading(false);
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">API Dokumentation</h1>
          <p className="page-subtitle">100% zuverlaessige Seed-Data API - keine externen Abhaengigkeiten</p>
        </div>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "var(--space-4)" }}>
        {/* Endpoints List */}
        <section className="panel">
          <h2 style={{ marginBottom: "var(--space-4)" }}>Verfuegbare Endpoints</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {endpoints.map((ep) => (
              <button
                key={ep.path}
                onClick={() => testEndpoint(ep.path)}
                style={{
                  padding: "var(--space-3)",
                  background: selectedEndpoint === ep.path ? "var(--color-primary)" : "var(--color-surface)",
                  color: selectedEndpoint === ep.path ? "white" : "var(--color-text)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                  textAlign: "left",
                  cursor: "pointer",
                }}
              >
                <div style={{ fontFamily: "monospace", fontSize: "var(--font-size-xs)" }}>{ep.path}</div>
                <div style={{ fontSize: "var(--font-size-sm)", marginTop: "var(--space-1)", opacity: 0.7 }}>
                  {ep.description}
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* Response Panel */}
        <section className="panel">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
            <h2>Response</h2>
            <span style={{ 
              fontSize: "var(--font-size-xs)", 
              fontFamily: "monospace",
              background: "var(--color-bg-muted)",
              padding: "var(--space-1) var(--space-2)",
              borderRadius: "var(--radius-sm)",
            }}>
              {selectedEndpoint}
            </span>
          </div>
          
          {loading ? (
            <div style={{ textAlign: "center", padding: "var(--space-6)" }}>
              <span className="muted">Laden...</span>
            </div>
          ) : (
            <pre style={{
              background: "var(--color-bg-muted)",
              padding: "var(--space-4)",
              borderRadius: "var(--radius-md)",
              overflow: "auto",
              maxHeight: "600px",
              fontSize: "var(--font-size-xs)",
              fontFamily: "monospace",
              lineHeight: 1.5,
            }}>
              {response || "Klicken Sie auf einen Endpoint um ihn zu testen."}
            </pre>
          )}
        </section>
      </div>

      {/* API Info */}
      <section className="panel" style={{ marginTop: "var(--space-4)" }}>
        <h2 style={{ marginBottom: "var(--space-4)" }}>API Uebersicht</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "var(--space-4)" }}>
          <div style={{ padding: "var(--space-4)", background: "var(--color-success-subtle)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600, color: "var(--color-success)" }}>13</div>
            <div className="muted">Kooperativen (PE, CO, ET, BR)</div>
          </div>
          <div style={{ padding: "var(--space-4)", background: "var(--color-info-subtle)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600, color: "var(--color-info)" }}>8</div>
            <div className="muted">Deutsche Roestereien</div>
          </div>
          <div style={{ padding: "var(--space-4)", background: "var(--color-warning-subtle)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600, color: "var(--color-warning)" }}>6</div>
            <div className="muted">Peru Anbauregionen</div>
          </div>
          <div style={{ padding: "var(--space-4)", background: "var(--color-primary-subtle)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: 600, color: "var(--color-primary)" }}>100%</div>
            <div className="muted">Zuverlaessigkeit (keine ext. APIs)</div>
          </div>
        </div>
      </section>

      {/* Data Source Info */}
      <section className="panel" style={{ marginTop: "var(--space-4)" }}>
        <h2 style={{ marginBottom: "var(--space-4)" }}>Datenquellen</h2>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
              <th style={{ textAlign: "left", padding: "var(--space-2)" }}>Datentyp</th>
              <th style={{ textAlign: "left", padding: "var(--space-2)" }}>Quelle</th>
              <th style={{ textAlign: "left", padding: "var(--space-2)" }}>Anzahl</th>
              <th style={{ textAlign: "left", padding: "var(--space-2)" }}>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
              <td style={{ padding: "var(--space-2)" }}>Kooperativen</td>
              <td style={{ padding: "var(--space-2)", fontFamily: "monospace", fontSize: "var(--font-size-xs)" }}>seed_demo_data.py</td>
              <td style={{ padding: "var(--space-2)" }}>13</td>
              <td style={{ padding: "var(--space-2)" }}><span style={{ color: "var(--color-success)" }}>Aktiv</span></td>
            </tr>
            <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
              <td style={{ padding: "var(--space-2)" }}>Roestereien</td>
              <td style={{ padding: "var(--space-2)", fontFamily: "monospace", fontSize: "var(--font-size-xs)" }}>seed_demo_data.py</td>
              <td style={{ padding: "var(--space-2)" }}>8</td>
              <td style={{ padding: "var(--space-2)" }}><span style={{ color: "var(--color-success)" }}>Aktiv</span></td>
            </tr>
            <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
              <td style={{ padding: "var(--space-2)" }}>Regionen</td>
              <td style={{ padding: "var(--space-2)", fontFamily: "monospace", fontSize: "var(--font-size-xs)" }}>seed_peru_regions.py</td>
              <td style={{ padding: "var(--space-2)" }}>6</td>
              <td style={{ padding: "var(--space-2)" }}><span style={{ color: "var(--color-success)" }}>Aktiv</span></td>
            </tr>
            <tr>
              <td style={{ padding: "var(--space-2)" }}>Marktdaten</td>
              <td style={{ padding: "var(--space-2)", fontFamily: "monospace", fontSize: "var(--font-size-xs)" }}>Statisch (Demo)</td>
              <td style={{ padding: "var(--space-2)" }}>-</td>
              <td style={{ padding: "var(--space-2)" }}><span style={{ color: "var(--color-success)" }}>Aktiv</span></td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  );
}
