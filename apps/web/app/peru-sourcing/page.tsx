"use client";

import { useState } from "react";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import { usePeruRegions, useCooperatives } from "../hooks/usePeruRegions";
import { CooperativeFilters } from "../types";

/* ============================================================
   PERU SOURCING INTELLIGENCE - ENTERPRISE VIEW
   ============================================================ */

function getScoreColor(score: number): string {
  if (score >= 80) return "badgeOk";
  if (score >= 60) return "badgeWarn";
  return "badgeErr";
}

export default function PeruSourcingDashboard() {
  const [filters, setFilters] = useState<Partial<CooperativeFilters>>({});
  const [showArchived, setShowArchived] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const { data: regions, isLoading: regionsLoading, refetch: refetchRegions } = usePeruRegions();
  const { data: coopsData, isLoading: coopsLoading, refetch: refetchCoops } = useCooperatives({
    ...filters,
    include_deleted: showArchived,
    limit: 50,
  });

  const cooperatives = coopsData?.items || [];

  const handleRefresh = () => {
    refetchRegions();
    refetchCoops();
  };

  async function archiveCoop(id: number) {
    if (!confirm("Kooperative archivieren?")) return;
    setBusyId(id);
    try {
      await apiFetch(`/cooperatives/${id}`, { method: "DELETE" });
      await refetchCoops();
    } catch (e) {
      console.error("Failed to archive cooperative:", e);
    } finally {
      setBusyId(null);
    }
  }

  async function restoreCoop(id: number) {
    setBusyId(id);
    try {
      await apiFetch(`/cooperatives/${id}/restore`, { method: "POST" });
      await refetchCoops();
    } catch (e) {
      console.error("Failed to restore cooperative:", e);
    } finally {
      setBusyId(null);
    }
  }

  // Stats
  const stats = {
    totalRegions: regions?.length || 0,
    totalCoops: cooperatives.filter(c => !c.deleted_at).length,
    totalCapacity: cooperatives.reduce((sum, c) => sum + (c.annual_production_kg || 0), 0),
    avgScore: cooperatives.length > 0
      ? cooperatives.reduce((sum, c) => sum + (c.quality_score || 0), 0) / cooperatives.length
      : 0,
  };

  return (
    <div className="page">
      <div className="content">
        {/* Page Header */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Peru Sourcing Intelligence</h1>
            <p className="subtitle">
              Entdecken Sie Kaffeeregionen, Kooperativen und Beschaffungschancen in Peru
            </p>
          </div>
          <div className="pageHeaderActions">
            <label className="checkboxLabel">
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
              />
              Archivierte anzeigen
            </label>
            <button type="button" className="btn" onClick={handleRefresh}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
                <path d="M16 21h5v-5"/>
              </svg>
              Aktualisieren
            </button>
            <Link href="/cooperatives" className="btn btnPrimary">
              Alle Kooperativen
            </Link>
          </div>
        </header>

        {/* KPI Grid */}
        <div className="kpiGrid">
          <div className="kpiCard">
            <span className="cardLabel">Kaffeeregionen</span>
            <span className="cardValue">{stats.totalRegions}</span>
            <span className="cardHint">Anbaugebiete in Peru</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Kooperativen</span>
            <span className="cardValue">{stats.totalCoops}</span>
            <span className="cardHint">Aktive Partner</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Kapazitaet Gesamt</span>
            <span className="cardValue">
              {stats.totalCapacity > 1000000 
                ? `${(stats.totalCapacity / 1000000).toFixed(1)}M`
                : stats.totalCapacity > 1000 
                  ? `${(stats.totalCapacity / 1000).toFixed(0)}t`
                  : stats.totalCapacity}
            </span>
            <span className="cardHint">kg pro Jahr</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Durchschn. Score</span>
            <span className="cardValue">{stats.avgScore.toFixed(1)}</span>
            <span className="cardHint">Qualitaetsbewertung</span>
          </div>
        </div>

        {/* Regions Panel */}
        <div className="panel" style={{ marginBottom: "var(--space-6)" }}>
          <div className="panelHeader">
            <h2 className="panelTitle">Peru Kaffeeregionen</h2>
            <span className="badge">
              {regionsLoading ? "..." : `${regions?.length || 0} Regionen`}
            </span>
          </div>
          <div className="panelBody">
            <div className="regionGrid">
              {(regions || []).map((region) => (
                <Link
                  key={region.id}
                  href={`/peru-sourcing/regions/${region.name}`}
                  className="regionCard"
                >
                  <div className="regionCardHeader">
                    <h3 className="regionCardTitle">{region.name}</h3>
                    {region.altitude_range && (
                      <span className="badge">{region.altitude_range}</span>
                    )}
                  </div>
                  <p className="regionCardDesc">
                    {region.description_de || "Peru-Kaffeeregion"}
                  </p>
                  {region.typical_varieties && (
                    <div className="regionCardMeta">
                      <span className="small muted">Sorten: {region.typical_varieties}</span>
                    </div>
                  )}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Filters Panel */}
        <div className="panel" style={{ marginBottom: "var(--space-6)" }}>
          <div className="panelHeader">
            <h2 className="panelTitle">Filter</h2>
            <button
              type="button"
              className="btn btnSm btnGhost"
              onClick={() => setFilters({})}
            >
              Zuruecksetzen
            </button>
          </div>
          <div className="panelBody">
            <div className="fieldGrid2">
              <div className="field">
                <label className="fieldLabel">Region</label>
                <select
                  className="input"
                  value={filters.region || ""}
                  onChange={(e) => setFilters({ ...filters, region: e.target.value || undefined })}
                >
                  <option value="">Alle Regionen</option>
                  {(regions || []).map((r) => (
                    <option key={r.id} value={r.name}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label className="fieldLabel">Min. Kapazitaet (kg)</label>
                <input
                  type="number"
                  className="input"
                  placeholder="z.B. 10000"
                  value={filters.min_capacity || ""}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      min_capacity: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
              </div>
              <div className="field">
                <label className="fieldLabel">Min. Qualitaetsscore</label>
                <input
                  type="number"
                  className="input"
                  placeholder="0-100"
                  min="0"
                  max="100"
                  value={filters.min_score || ""}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      min_score: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
              </div>
              <div className="field">
                <label className="fieldLabel">Zertifizierung</label>
                <select
                  className="input"
                  value={filters.certification || ""}
                  onChange={(e) => setFilters({ ...filters, certification: e.target.value || undefined })}
                >
                  <option value="">Alle</option>
                  <option value="Organic">Bio</option>
                  <option value="Fair Trade">Fair Trade</option>
                  <option value="Rainforest Alliance">Rainforest Alliance</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Cooperatives Table */}
        <div className="panel">
          <div className="panelHeader">
            <h2 className="panelTitle">Kooperativen-Verzeichnis</h2>
            <span className="badge">
              {coopsLoading ? "..." : `${cooperatives.length} Eintraege`}
            </span>
          </div>

          {cooperatives.length > 0 ? (
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Region</th>
                    <th>Mitglieder</th>
                    <th>Kapazitaet</th>
                    <th>Zertifizierungen</th>
                    <th>Score</th>
                    <th>Kontakt</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {cooperatives.map((coop) => (
                    <tr key={coop.id}>
                      <td>
                        <span style={{ fontWeight: 600 }}>{coop.name}</span>
                        {coop.deleted_at && (
                          <span className="badge badgeWarn" style={{ marginLeft: "var(--space-2)" }}>
                            Archiviert
                          </span>
                        )}
                      </td>
                      <td>{coop.region || "-"}</td>
                      <td>
                        {coop.members_count 
                          ? coop.members_count.toLocaleString() 
                          : "-"}
                      </td>
                      <td>
                        {coop.annual_production_kg 
                          ? `${(coop.annual_production_kg / 1000).toFixed(0)}t` 
                          : "-"}
                      </td>
                      <td>
                        {coop.certifications?.length > 0 ? (
                          <div style={{ display: "flex", gap: "var(--space-1)", flexWrap: "wrap" }}>
                            {coop.certifications.slice(0, 2).map((cert: string, i: number) => (
                              <span key={i} className="badge">{cert}</span>
                            ))}
                            {coop.certifications.length > 2 && (
                              <span className="badge">+{coop.certifications.length - 2}</span>
                            )}
                          </div>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td>
                        {coop.quality_score ? (
                          <span className={`badge ${getScoreColor(coop.quality_score)}`}>
                            {coop.quality_score}
                          </span>
                        ) : (
                          <span className="badge">-</span>
                        )}
                      </td>
                      <td>
                        {coop.contact_email || coop.contact_phone ? (
                          <span className="badge badgeOk">Vorhanden</span>
                        ) : (
                          <span className="badge">-</span>
                        )}
                      </td>
                      <td>
                        <div className="tableActions">
                          <Link href={`/cooperatives/${coop.id}`} className="btn btnSm btnGhost">
                            Details
                          </Link>
                          {coop.deleted_at ? (
                            <button
                              className="btn btnSm"
                              onClick={() => restoreCoop(coop.id)}
                              disabled={busyId === coop.id}
                            >
                              Wiederherstellen
                            </button>
                          ) : (
                            <button
                              className="btn btnSm btnDanger"
                              onClick={() => archiveCoop(coop.id)}
                              disabled={busyId === coop.id}
                            >
                              Archivieren
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="panelBody">
              <div className="emptyState">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.3, marginBottom: "var(--space-4)" }}>
                  <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/>
                </svg>
                <h3 className="h4">Keine Kooperativen gefunden</h3>
                <p className="subtitle">
                  Passen Sie die Filter an oder fuehren Sie Discovery Seed aus.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .regionGrid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: var(--space-4);
        }
        .regionCard {
          display: flex;
          flex-direction: column;
          padding: var(--space-4);
          background: var(--color-bg-subtle);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          transition: all 150ms ease;
          text-decoration: none;
        }
        .regionCard:hover {
          background: var(--color-bg-muted);
          border-color: var(--color-border-strong);
        }
        .regionCardHeader {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--space-2);
          margin-bottom: var(--space-2);
        }
        .regionCardTitle {
          font-size: var(--font-size-base);
          font-weight: var(--font-weight-semibold);
          color: var(--color-text);
          margin: 0;
        }
        .regionCardDesc {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
          line-height: var(--line-height-relaxed);
          margin: 0 0 var(--space-3);
          flex: 1;
        }
        .regionCardMeta {
          padding-top: var(--space-3);
          border-top: 1px solid var(--color-border);
        }
      `}</style>
    </div>
  );
}
