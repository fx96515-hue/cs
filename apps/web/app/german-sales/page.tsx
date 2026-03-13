"use client";

import { useState } from "react";
import Link from "next/link";
import { useRoasters } from "../hooks/useRoasters";
import { RoasterFilters } from "../types";
import { format } from "date-fns";

/* ============================================================
   GERMAN SALES DASHBOARD - ENTERPRISE VIEW
   ============================================================ */

function getScoreColor(score: number): string {
  if (score >= 80) return "badgeOk";
  if (score >= 60) return "badgeWarn";
  return "badgeErr";
}

function getStatusBadge(status: string | null | undefined): { className: string; label: string } {
  const statusMap: Record<string, { className: string; label: string }> = {
    contacted: { className: "badgeInfo", label: "Kontaktiert" },
    in_conversation: { className: "badgeInfo", label: "Im Gespraech" },
    qualified: { className: "badgeOk", label: "Qualifiziert" },
    proposal: { className: "badgeWarn", label: "Angebot" },
    negotiation: { className: "badgeWarn", label: "Verhandlung" },
    closed_won: { className: "badgeOk", label: "Gewonnen" },
    closed_lost: { className: "badgeErr", label: "Verloren" },
  };
  return statusMap[status || ""] || { className: "badge", label: status || "Neu" };
}

export default function GermanSalesDashboard() {
  const [filters, setFilters] = useState<Partial<RoasterFilters>>({
    country: "Germany",
  });

  const { data: roastersData, isLoading, refetch } = useRoasters({ ...filters, limit: 100 });
  const roasters = roastersData?.items || [];

  const stats = {
    total: roasters.length,
    contacted: roasters.filter(
      (r) => r.contact_status === "contacted" || r.contact_status === "in_conversation",
    ).length,
    qualified: roasters.filter(
      (r) => r.contact_status === "qualified" || r.contact_status === "proposal",
    ).length,
    avgSalesScore:
      roasters.length > 0
        ? roasters.reduce((sum, r) => sum + (r.sales_fit_score || 0), 0) / roasters.length
        : 0,
  };

  const priorityRoasters = roasters
    .filter((r) => (r.overall_score || 0) >= 70)
    .sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0))
    .slice(0, 10);

  const pendingFollowups = roasters.filter((r) => {
    if (!r.next_followup_date) return false;
    const followupDate = new Date(r.next_followup_date);
    return followupDate <= new Date();
  });

  return (
    <div className="page">
      <div className="content">
        {/* Page Header */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Deutschland Vertrieb</h1>
            <p className="subtitle">
              Beziehungen und Vertriebschancen mit deutschen Spezialitaetenroestern verwalten
            </p>
          </div>
          <div className="pageHeaderActions">
            <button type="button" className="btn" onClick={() => refetch()}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
                <path d="M16 21h5v-5"/>
              </svg>
              Aktualisieren
            </button>
            <Link href="/roasters" className="btn btnPrimary">
              Alle Röstereien
            </Link>
          </div>
        </header>

        {/* KPI Grid */}
        <div className="kpiGrid">
          <div className="kpiCard">
            <span className="cardLabel">Röstereien Gesamt</span>
            <span className="cardValue">{stats.total}</span>
            <span className="cardHint">In CRM-Datenbank</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">In Pipeline</span>
            <span className="cardValue">{stats.contacted}</span>
            <span className="cardHint">Kontaktiert oder im Gespraech</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Qualifiziert</span>
            <span className="cardValue">{stats.qualified}</span>
            <span className="cardHint">Bereit für Angebote</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Durchschn. Sales Score</span>
            <span className="cardValue">{stats.avgSalesScore.toFixed(1)}</span>
            <span className="cardHint">Von 100 Punkten</span>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid2col">
          {/* Priority Contacts */}
          <div className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Prioritaetskontakte</h2>
              <span className="badge">{priorityRoasters.length}</span>
            </div>
            <div className="panelBody">
              <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
                Top 10 Röstereien nach Vertriebs-Fit-Score
              </p>
              {priorityRoasters.length > 0 ? (
                <div className="list">
                  {priorityRoasters.map((roaster) => (
                    <Link 
                      key={roaster.id} 
                      href={`/roasters/${roaster.id}`}
                      className="listItem"
                      style={{ textDecoration: "none" }}
                    >
                      <div className="listMain">
                        <div className="listTitle">{roaster.company_name}</div>
                        <div className="listMeta">
                          <span>{roaster.city || "Deutschland"}</span>
                          {roaster.roaster_type && (
                            <>
                              <span className="dot">·</span>
                              <span>{roaster.roaster_type}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <span className={`badge ${getScoreColor(roaster.sales_fit_score || 0)}`}>
                        {roaster.sales_fit_score}
                      </span>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="emptyState">
                  <p>Keine Prioritaetskontakte gefunden</p>
                </div>
              )}
            </div>
          </div>

          {/* Pending Followups */}
          <div className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Ausstehende Nachverfolgungen</h2>
              <span className={`badge ${pendingFollowups.length > 0 ? "badgeWarn" : "badgeOk"}`}>
                {pendingFollowups.length}
              </span>
            </div>
            <div className="panelBody">
              <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
                Röstereien mit faelliger Nachverfolgung
              </p>
              {pendingFollowups.length > 0 ? (
                <div className="list">
                  {pendingFollowups.slice(0, 10).map((roaster) => (
                    <Link 
                      key={roaster.id} 
                      href={`/roasters/${roaster.id}`}
                      className="listItem"
                      style={{ textDecoration: "none" }}
                    >
                      <div className="listMain">
                        <div className="listTitle">{roaster.company_name}</div>
                        <div className="listMeta">
                          <span>{roaster.city || "Deutschland"}</span>
                          {roaster.next_followup_date && (
                            <>
                              <span className="dot">·</span>
                              <span>Faellig: {format(new Date(roaster.next_followup_date), "dd.MM.")}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <span className="badge badgeErr">Ueberfaellig</span>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="emptyState">
                  <p>Alles erledigt - keine ausstehenden Nachverfolgungen</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Filters Panel */}
        <div className="panel" style={{ marginTop: "var(--space-6)" }}>
          <div className="panelHeader">
            <h2 className="panelTitle">Filter</h2>
            <button
              type="button"
              className="btn btnSm btnGhost"
              onClick={() => setFilters({ country: "Germany" })}
            >
              Zuruecksetzen
            </button>
          </div>
          <div className="panelBody">
            <div className="fieldGrid2">
              <div className="field">
                <label className="fieldLabel">Stadt</label>
                <input
                  type="text"
                  className="input"
                  placeholder="z.B. Berlin, Hamburg"
                  value={filters.city || ""}
                  onChange={(e) => setFilters({ ...filters, city: e.target.value || undefined })}
                />
              </div>
              <div className="field">
                <label className="fieldLabel">Roestertyp</label>
                <select
                  className="input"
                  value={filters.roaster_type || ""}
                  onChange={(e) => setFilters({ ...filters, roaster_type: e.target.value || undefined })}
                >
                  <option value="">Alle Typen</option>
                  <option value="Specialty">Spezialitaet</option>
                  <option value="Commercial">Kommerziell</option>
                  <option value="Micro">Mikro</option>
                </select>
              </div>
              <div className="field">
                <label className="fieldLabel">Min. Sales Score</label>
                <input
                  type="number"
                  className="input"
                  placeholder="0-100"
                  min="0"
                  max="100"
                  value={filters.min_sales_fit_score || ""}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      min_sales_fit_score: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
              </div>
              <div className="field">
                <label className="fieldLabel">Kontaktstatus</label>
                <select
                  className="input"
                  value={filters.contact_status || ""}
                  onChange={(e) => setFilters({ ...filters, contact_status: e.target.value || undefined })}
                >
                  <option value="">Alle Status</option>
                  <option value="contacted">Kontaktiert</option>
                  <option value="in_conversation">Im Gespraech</option>
                  <option value="qualified">Qualifiziert</option>
                  <option value="proposal">Angebot</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Main Table */}
        <div className="panel" style={{ marginTop: "var(--space-6)" }}>
          <div className="panelHeader">
            <h2 className="panelTitle">Alle Röstereien</h2>
            <span className="badge">
              {isLoading ? "..." : `${roasters.length} Eintraege`}
            </span>
          </div>
          
          {roasters.length > 0 ? (
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Unternehmen</th>
                    <th>Stadt</th>
                    <th>Typ</th>
                    <th>Kapazitaet</th>
                    <th>Sales Score</th>
                    <th>Status</th>
                    <th>Letzter Kontakt</th>
                    <th>Naechste Aktion</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {roasters.map((roaster) => {
                    const status = getStatusBadge(roaster.contact_status);
                    return (
                      <tr key={roaster.id}>
                        <td>
                          <span style={{ fontWeight: 600 }}>{roaster.company_name}</span>
                        </td>
                        <td>{roaster.city || "-"}</td>
                        <td>{roaster.roaster_type || "-"}</td>
                        <td>
                          {roaster.annual_capacity_kg
                            ? `${(roaster.annual_capacity_kg / 1000).toFixed(0)}t`
                            : "-"}
                        </td>
                        <td>
                          {roaster.sales_fit_score ? (
                            <span className={`badge ${getScoreColor(roaster.sales_fit_score)}`}>
                              {roaster.sales_fit_score}
                            </span>
                          ) : (
                            <span className="badge">-</span>
                          )}
                        </td>
                        <td>
                          <span className={`badge ${status.className}`}>{status.label}</span>
                        </td>
                        <td>
                          {roaster.last_contact_date
                            ? format(new Date(roaster.last_contact_date), "dd.MM.yy")
                            : "-"}
                        </td>
                        <td>
                          {roaster.next_followup_date ? (
                            <span
                              className={`badge ${
                                new Date(roaster.next_followup_date) <= new Date()
                                  ? "badgeErr"
                                  : ""
                              }`}
                            >
                              {format(new Date(roaster.next_followup_date), "dd.MM.")}
                            </span>
                          ) : (
                            "-"
                          )}
                        </td>
                        <td>
                          <Link href={`/roasters/${roaster.id}`} className="btn btnSm btnGhost">
                            Details
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="panelBody">
              <div className="emptyState">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.3, marginBottom: "var(--space-4)" }}>
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <h3 className="h4">Keine Röstereien gefunden</h3>
                <p className="subtitle">
                  Führen Sie Discovery Seed unter Betrieb aus, um die Datenbank zu befüllen.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
