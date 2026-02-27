"use client";

import { useState } from "react";
import Link from "next/link";
import { useRoasters } from "../hooks/useRoasters";
import { RoasterFilters } from "../types";
import { format } from "date-fns";

export default function GermanSalesDashboard() {
  const [filters, setFilters] = useState<RoasterFilters>({
    country: "Germany",
  });

  const { data: roastersData, isLoading, refetch } = useRoasters({ ...filters, limit: 100 });
  const roasters = roastersData?.items || [];

  // Calculate pipeline stats
  const stats = {
    total: roasters.length,
    contacted: roasters.filter((r) => r.contact_status === "contacted" || r.contact_status === "in_conversation").length,
    qualified: roasters.filter((r) => r.contact_status === "qualified" || r.contact_status === "proposal").length,
    avgSalesScore: roasters.length > 0
      ? roasters.reduce((sum, r) => sum + (r.sales_fit_score || 0), 0) / roasters.length
      : 0,
  };

  // Priority roasters (high score, not yet contacted or needs followup)
  const priorityRoasters = roasters
    .filter((r) => (r.overall_score || 0) >= 70)
    .sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0))
    .slice(0, 10);

  // Pending followups (roasters with past followup dates)
  const pendingFollowups = roasters.filter((r) => {
    if (!r.next_followup_date) return false;
    const followupDate = new Date(r.next_followup_date);
    return followupDate <= new Date();
  });

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Deutsche Röstereien Vertriebspipeline</div>
          <div className="muted">
            Verwalten Sie Beziehungen und Vertriebsmöglichkeiten mit deutschen Spezialitätenröstern
          </div>
        </div>
        <div className="actions">
          <button type="button" className="btn btnPrimary" onClick={() => refetch()}>
            Aktualisieren
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gridCols4" style={{ marginBottom: "18px" }}>
        <div className="panel card">
          <div className="cardLabel">Röstereien gesamt</div>
          <div className="cardValue">{stats.total}</div>
          <div className="cardHint">In CRM-Datenbank</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">In Pipeline</div>
          <div className="cardValue">{stats.contacted}</div>
          <div className="cardHint">Kontaktiert oder im Gespräch</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Qualifiziert</div>
          <div className="cardValue">{stats.qualified}</div>
          <div className="cardHint">Bereit für Angebote</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Durchschn. Vertriebs-Score</div>
          <div className="cardValue">{stats.avgSalesScore.toFixed(1)}</div>
          <div className="cardHint">Von 100</div>
        </div>
      </div>

      <div className="grid gridCols2" style={{ marginBottom: "18px" }}>
        {/* Priority Contact List */}
        <div className="panel" style={{ padding: "18px" }}>
          <div className="h2">Prioritätskontakte</div>
          <div className="muted" style={{ marginBottom: "14px" }}>
            Top 10 Röstereien nach Vertriebs-Fit-Score
          </div>
          {priorityRoasters.length > 0 ? (
            <div className="list">
              {priorityRoasters.map((roaster) => (
                <div key={roaster.id} className="listRow">
                  <div className="listMain">
                    <div className="listTitle">{roaster.company_name}</div>
                    <div className="listMeta">
                      <span>{roaster.city || "Germany"}</span>
                      {roaster.roaster_type && (
                        <>
                          <span className="dot">•</span>
                          <span>{roaster.roaster_type}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <span
                    className="badge"
                    style={{
                      background: "rgba(200,149,108,0.12)",
                      borderColor: "rgba(200,149,108,0.35)",
                    }}
                  >
                    Score: {roaster.sales_fit_score}
                  </span>
                  <Link href={`/roasters/${roaster.id}`} className="link">
                    Ansehen →
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty">Keine Prioritätskontakte gefunden</div>
          )}
        </div>

        {/* Pending Followups */}
        <div className="panel" style={{ padding: "18px" }}>
          <div className="h2">Ausstehende Nachverfolgungen</div>
          <div className="muted" style={{ marginBottom: "14px" }}>
            Röstereien, die heute oder überfällig eine Nachverfolgung benötigen
          </div>
          {pendingFollowups.length > 0 ? (
            <div className="list">
              {pendingFollowups.slice(0, 10).map((roaster) => (
                <div key={roaster.id} className="listRow">
                  <div className="listMain">
                    <div className="listTitle">{roaster.company_name}</div>
                    <div className="listMeta">
                      <span>{roaster.city || "Germany"}</span>
                      {roaster.next_followup_date && (
                        <>
                          <span className="dot">•</span>
                          <span>Fällig: {format(new Date(roaster.next_followup_date), "MMM dd")}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <span className="badge badgeWarn">Nachverfolgung</span>
                  <Link href={`/roasters/${roaster.id}`} className="link">
                    Aktion →
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty">Alles erledigt! Keine ausstehenden Nachverfolgungen.</div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="panel" style={{ padding: "18px", marginBottom: "18px" }}>
        <div className="h2">Röstereien filtern</div>
        <div className="grid gridCols4" style={{ marginTop: "14px", gap: "10px" }}>
          <div>
            <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
              Stadt
            </label>
            <input
              type="text"
              className="input"
              placeholder="z.B. Berlin"
              value={filters.city || ""}
              onChange={(e) =>
                setFilters({ ...filters, city: e.target.value || undefined })
              }
            />
          </div>
          <div>
            <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
              Röstertyp
            </label>
            <select
              className="input"
              value={filters.roaster_type || ""}
              onChange={(e) =>
                setFilters({ ...filters, roaster_type: e.target.value || undefined })
              }
            >
              <option value="">Alle Typen</option>
              <option value="Specialty">Spezialität</option>
              <option value="Commercial">Kommerziell</option>
              <option value="Micro">Mikro</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
              Min. Vertriebs-Score
            </label>
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
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button
              type="button"
              className="btn"
              onClick={() => setFilters({ country: "Germany" })}
              style={{ width: "100%" }}
            >
              Filter löschen
            </button>
          </div>
        </div>
      </div>

      {/* Roasters Table */}
      <div className="panel" style={{ padding: "18px" }}>
        <div className="h2">Alle Röstereien</div>
        <div className="muted" style={{ marginBottom: "14px" }}>
          {isLoading ? "Lade Röstereien..." : `${roasters.length} Röstereien gefunden`}
        </div>

        {roasters.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Firma</th>
                  <th>Stadt</th>
                  <th>Typ</th>
                  <th>Kapazität (kg)</th>
                  <th>Vertriebs-Score</th>
                  <th>Kontaktstatus</th>
                  <th>Letzter Kontakt</th>
                  <th>Nächste Nachverfolgung</th>
                  <th>Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {roasters.map((roaster) => (
                  <tr key={roaster.id}>
                    <td style={{ fontWeight: "600" }}>{roaster.company_name}</td>
                    <td>{roaster.city || "–"}</td>
                    <td>{roaster.roaster_type || "–"}</td>
                    <td>{roaster.annual_capacity_kg?.toLocaleString() || "–"}</td>
                    <td>
                      {roaster.sales_fit_score ? (
                        <span
                          className="badge"
                          style={{
                            background:
                              roaster.sales_fit_score >= 80
                                ? "rgba(64,214,123,0.12)"
                                : roaster.sales_fit_score >= 60
                                ? "rgba(255,183,64,0.12)"
                                : "rgba(255,92,92,0.12)",
                            borderColor:
                              roaster.sales_fit_score >= 80
                                ? "rgba(64,214,123,0.35)"
                                : roaster.sales_fit_score >= 60
                                ? "rgba(255,183,64,0.35)"
                                : "rgba(255,92,92,0.35)",
                          }}
                        >
                          {roaster.sales_fit_score}
                        </span>
                      ) : (
                        "–"
                      )}
                    </td>
                    <td>
                      {roaster.contact_status ? (
                        <span className="badge">{roaster.contact_status}</span>
                      ) : (
                        <span className="badge">neu</span>
                      )}
                    </td>
                    <td>
                      {roaster.last_contact_date
                        ? format(new Date(roaster.last_contact_date), "MMM dd, yyyy")
                        : "–"}
                    </td>
                    <td>
                      {roaster.next_followup_date ? (
                        <span
                          className={
                            new Date(roaster.next_followup_date) <= new Date()
                              ? "badge badgeErr"
                              : "badge"
                          }
                        >
                          {format(new Date(roaster.next_followup_date), "MMM dd")}
                        </span>
                      ) : (
                        "–"
                      )}
                    </td>
                    <td>
                      <Link href={`/roasters/${roaster.id}`} className="link">
                        Ansehen →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty" style={{ padding: "40px", textAlign: "center", color: "var(--muted)" }}>
            Keine Röstereien gefunden. Führen Sie Discovery Seed in Betrieb aus, um die Datenbank zu füllen.
          </div>
        )}
      </div>
    </div>
  );
}
