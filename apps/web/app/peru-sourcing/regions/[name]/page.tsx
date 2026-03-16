"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "../../../../lib/api";
import { usePeruRegionIntelligence, useCooperatives } from "../../../hooks/usePeruRegions";
import { ErrorPanel } from "../../../components/AlertError";
import { PageHeader } from "../../../components/PageHeader";

export default function RegionDetailPage() {
  const params = useParams();
  const regionName = params?.name as string;
  const [showArchived, setShowArchived] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const { data: region, isLoading, error } = usePeruRegionIntelligence(regionName);
  const { data: coopsData, refetch: refetchCoops } = useCooperatives({
    region: regionName,
    include_deleted: showArchived,
    limit: 100,
  });
  const cooperatives = coopsData?.items || [];

  if (isLoading) {
    return (
      <div className="content">
        <div className="panel">Lade Region...</div>
      </div>
    );
  }

  if (error || !region) {
    return (
      <div className="content">
        <div className="panel">
          <ErrorPanel message="Region nicht gefunden oder Fehler beim Laden." compact />
          <div
            className="pageHeaderActions"
            style={{ marginTop: "var(--space-3)" }}
          >
            <Link href="/peru-sourcing" className="btn">
              Zurueck zur Uebersicht
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const getScoreBadgeClass = (score: number | null | undefined): string => {
    if (!score && score !== 0) return "badge";
    if (score >= 80) return "badge badgeOk";
    if (score >= 60) return "badge badgeWarn";
    return "badge badgeErr";
  };

  const getRiskBadgeClass = (riskText: string | null | undefined): string => {
    if (!riskText) return "badge";
    const lower = riskText.toLowerCase();
    if (lower.includes("niedrig") || lower.includes("low")) return "badge badgeOk";
    if (lower.includes("mittel") || lower.includes("medium")) return "badge badgeWarn";
    if (lower.includes("hoch") || lower.includes("high")) return "badge badgeErr";
    return "badge";
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

  return (
    <div className="content">
      <PageHeader
        title={region.name}
        subtitle={`${region.country} | ${region.description || "Kaffeeanbaugebiet"}`}
        actions={
          <>
            <div className={getScoreBadgeClass(region.scores?.quality_consistency)}>
              Qualitaet: {region.scores?.quality_consistency?.toFixed(0) || "-"}
            </div>
            {region.production?.share_pct && (
              <div className="badge">
                {region.production.share_pct.toLocaleString("de-DE", {
                  maximumFractionDigits: 1,
                })}
                % Marktanteil
              </div>
            )}
            <Link href="/peru-sourcing" className="btn">
              Zurueck
            </Link>
          </>
        }
      />

      <div className="gridKpi">
        <div className="panel card">
          <div className="cardLabel">Hoehenlage</div>
          <div className="cardValue">
            {region.elevation_range?.min_m && region.elevation_range?.max_m
              ? `${region.elevation_range.min_m.toLocaleString("de-DE")} - ${region.elevation_range.max_m.toLocaleString("de-DE")} m`
              : "-"}
          </div>
          <div className="cardHint">Anbauhoehe ueber NN</div>
        </div>

        <div className="panel card">
          <div className="cardLabel">Jahresproduktion</div>
          <div className="cardValue">
            {region.production?.volume_kg
              ? `${(region.production.volume_kg / 1000).toLocaleString("de-DE", { maximumFractionDigits: 0 })} t`
              : "-"}
          </div>
          <div className="cardHint">Gesamtvolumen pro Jahr</div>
        </div>

        <div className="panel card">
          <div className="cardLabel">Qualitaetskonsistenz</div>
          <div className="cardValue">
            {region.quality?.consistency_score?.toFixed(0) || "-"}
          </div>
          <div className="cardHint">Score von 100</div>
        </div>

        <div className="panel card">
          <div className="cardLabel">Infrastruktur</div>
          <div className="cardValue">
            {region.logistics?.infrastructure_score?.toFixed(0) || "-"}
          </div>
          <div className="cardHint">Logistik-Score von 100</div>
        </div>
      </div>

      <div className="grid gridCols2">
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div className="panel" style={{ padding: "18px" }}>
            <div className="h2">Anbaubedingungen</div>
            <div className="muted" style={{ marginBottom: "14px" }}>
              Score: {region.scores?.growing_conditions?.toFixed(1) || "-"} / 100
            </div>

            <div style={{ display: "grid", gap: "12px" }}>
              <div>
                <div className="cardLabel">Klima</div>
                <div style={{ fontSize: "14px", marginTop: "6px" }}>
                  {region.climate?.avg_temperature_c && (
                    <div>Temperatur: {region.climate.avg_temperature_c.toLocaleString("de-DE")} C</div>
                  )}
                  {region.climate?.rainfall_mm && (
                    <div>Niederschlag: {region.climate.rainfall_mm.toLocaleString("de-DE")} mm</div>
                  )}
                  {region.climate?.humidity_pct && (
                    <div>Luftfeuchtigkeit: {region.climate.humidity_pct.toLocaleString("de-DE")}%</div>
                  )}
                </div>
              </div>

              {region.soil_type && (
                <div>
                  <div className="cardLabel">Bodentyp</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>{region.soil_type}</div>
                </div>
              )}

              <div>
                <div className="cardLabel">Hoehenlage</div>
                <div style={{ fontSize: "14px", marginTop: "6px" }}>
                  {region.elevation_range?.min_m && region.elevation_range?.max_m
                    ? `${region.elevation_range.min_m.toLocaleString("de-DE")} - ${region.elevation_range.max_m.toLocaleString("de-DE")} m ü. NN`
                    : "Keine Daten"}
                </div>
              </div>
            </div>
          </div>

          <div className="panel" style={{ padding: "18px" }}>
            <div className="h2">Qualitaetsprofil</div>
            <div className="muted" style={{ marginBottom: "14px" }}>Typische Qualitaetsmerkmale</div>

            <div style={{ display: "grid", gap: "12px" }}>
              {region.quality?.typical_varieties && (
                <div>
                  <div className="cardLabel">Typische Sorten</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>{region.quality.typical_varieties}</div>
                </div>
              )}

              {region.quality?.typical_processing && (
                <div>
                  <div className="cardLabel">Aufbereitungsmethoden</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>{region.quality.typical_processing}</div>
                </div>
              )}

              {region.quality?.profile && (
                <div>
                  <div className="cardLabel">Geschmacksprofil</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>{region.quality.profile}</div>
                </div>
              )}

              {region.quality?.consistency_score && (
                <div>
                  <div className="cardLabel">SCA Score-Bereich</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>
                    ~{region.quality.consistency_score.toFixed(0)} Punkte
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="panel" style={{ padding: "18px" }}>
            <div className="h2">Produktionsdaten</div>
            <div className="muted" style={{ marginBottom: "14px" }}>Regionale Produktionskapazitaet</div>

            <div style={{ display: "grid", gap: "12px" }}>
              {region.production?.volume_kg && (
                <div>
                  <div className="cardLabel">Jahresvolumen</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>
                    {region.production.volume_kg.toLocaleString("de-DE")} kg
                  </div>
                </div>
              )}

              {region.production?.share_pct && (
                <div>
                  <div className="cardLabel">Marktanteil Peru</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>
                    {region.production.share_pct.toLocaleString("de-DE", { maximumFractionDigits: 1 })}%
                  </div>
                </div>
              )}

              {region.production?.harvest_months && (
                <div>
                  <div className="cardLabel">Erntezeit</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>{region.production.harvest_months}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div className="panel" style={{ padding: "18px" }}>
            <div className="h2">Logistik & Infrastruktur</div>
            <div className="muted" style={{ marginBottom: "14px" }}>
              Score: {region.logistics?.infrastructure_score?.toFixed(0) || "-"} / 100
            </div>

            <div style={{ display: "grid", gap: "12px" }}>
              {region.logistics?.main_port && (
                <div>
                  <div className="cardLabel">Naechster Hafen</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>{region.logistics.main_port}</div>
                </div>
              )}

              {region.logistics?.transport_time_hours && (
                <div>
                  <div className="cardLabel">Transport nach Callao</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>
                    ~{region.logistics.transport_time_hours.toLocaleString("de-DE")} Stunden
                  </div>
                </div>
              )}

              {region.logistics?.cost_per_kg && (
                <div>
                  <div className="cardLabel">Logistikkosten</div>
                  <div style={{ fontSize: "14px", marginTop: "6px" }}>
                    ${region.logistics.cost_per_kg.toLocaleString("de-DE", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })} pro kg
                  </div>
                </div>
              )}

              <div>
                <div className="cardLabel">Infrastruktur-Bewertung</div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "6px" }}>
                  <div className={getScoreBadgeClass(region.logistics?.infrastructure_score)}>
                    {region.logistics?.infrastructure_score?.toFixed(0) || "-"}
                  </div>
                  <span style={{ fontSize: "13px", color: "var(--muted)" }}>von 100 Punkten</span>
                </div>
              </div>
            </div>
          </div>

          <div className="panel" style={{ padding: "18px" }}>
            <div className="h2">Risikoeinschaetzung</div>
            <div className="muted" style={{ marginBottom: "14px" }}>Bewertung der Hauptrisiken</div>

            <div style={{ display: "grid", gap: "12px" }}>
              {region.risks?.weather && (
                <div>
                  <div className="cardLabel">Wetterrisiko</div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "6px" }}>
                    <div className={getRiskBadgeClass(region.risks.weather)}>{region.risks.weather}</div>
                  </div>
                </div>
              )}

              {region.risks?.political && (
                <div>
                  <div className="cardLabel">Politisches Risiko</div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "6px" }}>
                    <div className={getRiskBadgeClass(region.risks.political)}>{region.risks.political}</div>
                  </div>
                </div>
              )}

              {region.risks?.logistics && (
                <div>
                  <div className="cardLabel">Logistikrisiko</div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "6px" }}>
                    <div className={getRiskBadgeClass(region.risks.logistics)}>{region.risks.logistics}</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="panel" style={{ padding: "18px" }}>
            <div className="h2">Aktive Kooperativen</div>
            <div className="muted" style={{ marginBottom: "14px" }}>
              {cooperatives.length} Kooperativen in dieser Region
            </div>
            <div className="row" style={{ marginBottom: 10 }}>
              <label className="row" style={{ gap: 6 }}>
                <input
                  type="checkbox"
                  checked={showArchived}
                  onChange={(e) => setShowArchived(e.target.checked)}
                />
                <span className="small muted">Archivierte anzeigen</span>
              </label>
            </div>

            {cooperatives.length > 0 ? (
              <div className="list">
                {cooperatives.map((coop) => (
                  <div key={coop.id} className="listRow">
                    <div className="listMain">
                      <div className="listTitle">
                        <Link className="link" href={`/cooperatives/${coop.id}`}>
                          {coop.name}
                        </Link>
                        {coop.deleted_at ? (
                          <span style={{ marginLeft: 8 }} className="badge badgeWarn">
                            archiviert
                          </span>
                        ) : null}
                      </div>
                      <div className="listMeta">
                        {coop.members_count && (
                          <span>{coop.members_count.toLocaleString("de-DE")} Mitglieder</span>
                        )}
                        {coop.members_count && coop.annual_production_kg && (
                          <span className="dot">|</span>
                        )}
                        {coop.annual_production_kg && (
                          <span>
                            {(coop.annual_production_kg / 1000).toLocaleString("de-DE", { maximumFractionDigits: 0 })} t/Jahr
                          </span>
                        )}
                      </div>
                    </div>
                    {coop.quality_score && (
                      <div className={getScoreBadgeClass(coop.quality_score)}>{coop.quality_score}</div>
                    )}
                    <div className="row" style={{ gap: 6 }}>
                      {coop.deleted_at ? (
                        <button
                          className="btn"
                          onClick={() => restoreCoop(coop.id)}
                          disabled={busyId === coop.id}
                        >
                          Restore
                        </button>
                      ) : (
                        <button
                          className="btn"
                          onClick={() => archiveCoop(coop.id)}
                          disabled={busyId === coop.id}
                        >
                          Archivieren
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty">Keine Kooperativen in dieser Region gefunden.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
