"use client";

import React, { useState } from "react";
import { format, differenceInDays } from "date-fns";
import { useShipments, useCreateShipment } from "../hooks/useShipments";
import { apiFetch } from "../../lib/api";
import { ErrorPanel } from "../components/AlertError";
import { Shipment } from "../types";

/* ============================================================
   SHIPMENTS TRACKING - ENTERPRISE VIEW
   ============================================================ */

export default function ShipmentsDashboard() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [createForm, setCreateForm] = useState({
    container_number: "",
    bill_of_lading: "",
    weight_kg: 18000,
    container_type: "40ft",
    origin_port: "Callao, Peru",
    destination_port: "Hamburg, Germany",
    departure_date: "",
    estimated_arrival: "",
    notes: "",
    lot_ids: "",
  });

  const { data: shipmentsResponse, isLoading, error, refetch } = useShipments({
    limit: 200,
    include_deleted: showArchived,
  });
  const createShipment = useCreateShipment();
  const [now] = useState(() => Date.now());

  const shipments = shipmentsResponse?.items ?? [];
  const activeShipments = shipments.filter((s) => !s.deleted_at);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const parsedLotIds = createForm.lot_ids
        ? createForm.lot_ids
            .split(",")
            .map((v) => Number(v.trim()))
            .filter((v) => Number.isFinite(v) && v > 0)
        : null;
      const lotIds = parsedLotIds && parsedLotIds.length > 0 ? parsedLotIds : null;

      await createShipment.mutateAsync({
        ...createForm,
        lot_id: null,
        cooperative_id: null,
        roaster_id: null,
        weight_kg: Number(createForm.weight_kg),
        departure_date: createForm.departure_date || null,
        estimated_arrival: createForm.estimated_arrival || null,
        notes: createForm.notes || null,
        lot_ids: lotIds,
      });
      setShowCreateModal(false);
      setCreateForm({
        container_number: "",
        bill_of_lading: "",
        weight_kg: 18000,
        container_type: "40ft",
        origin_port: "Callao, Peru",
        destination_port: "Hamburg, Germany",
        departure_date: "",
        estimated_arrival: "",
        notes: "",
        lot_ids: "",
      });
      await refetch();
    } catch (createError) {
      console.error("Failed to create shipment:", createError);
    }
  };

  const stats = {
    total: activeShipments.length,
    inTransit: activeShipments.filter((s) => s.status === "in_transit").length,
    arrived: activeShipments.filter((s) => s.status === "delivered" || s.status === "arrived").length,
    totalWeight: activeShipments.reduce((sum, s) => sum + (s.weight_kg || 0), 0),
  };

  async function archiveShipment(id: number) {
    if (!confirm("Sendung archivieren?")) return;
    try {
      await apiFetch(`/shipments/${id}`, { method: "DELETE" });
      await refetch();
    } catch (archiveError) {
      console.error("Failed to archive shipment:", archiveError);
    }
  }

  async function restoreShipment(id: number) {
    try {
      await apiFetch(`/shipments/${id}/restore`, { method: "POST" });
      await refetch();
    } catch (restoreError) {
      console.error("Failed to restore shipment:", restoreError);
    }
  }

  const calculateProgress = (shipment: Shipment): number => {
    if (now === 0) return 0;
    if (shipment.status === "arrived" || shipment.actual_arrival) return 100;
    const eta = shipment.estimated_arrival || shipment.eta;
    if (!shipment.departure_date || !eta) return 0;

    const departure = new Date(shipment.departure_date).getTime();
    const etaTime = new Date(eta).getTime();

    if (now < departure) return 0;
    if (now >= etaTime) return 100;

    const totalDuration = etaTime - departure;
    const elapsed = now - departure;
    return Math.round((elapsed / totalDuration) * 100);
  };

  const arrivingSoon = activeShipments.filter((s) => {
    const eta = s.estimated_arrival || s.eta;
    if (s.status !== "in_transit" || !eta) return false;
    const daysUntilArrival = differenceInDays(new Date(eta), new Date());
    return daysUntilArrival >= 0 && daysUntilArrival <= 7;
  });

  const getStatusBadge = (status: string): { className: string; label: string } => {
    const map: Record<string, { className: string; label: string }> = {
      in_transit: { className: "badgeInfo", label: "In Transit" },
      arrived: { className: "badgeOk", label: "Angekommen" },
      delivered: { className: "badgeOk", label: "Geliefert" },
      delayed: { className: "badgeWarn", label: "Verspaetet" },
      pending: { className: "badge", label: "Ausstehend" },
    };
    return map[status] || { className: "badge", label: status };
  };

  if (isLoading) {
    return (
      <div className="page">
        <div className="content">
          <header className="pageHeader">
            <div className="pageHeaderContent">
              <h1 className="h1">Sendungsverfolgung</h1>
            </div>
          </header>
          <div className="panel">
            <div className="panelBody">
              <div className="loading">
                <div className="spinner"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="content">
          <header className="pageHeader">
            <div className="pageHeaderContent">
              <h1 className="h1">Sendungsverfolgung</h1>
            </div>
          </header>
          <ErrorPanel
            compact
            message={`Fehler beim Laden der Sendungen: ${String(error)}`}
            onRetry={() => {
              void refetch();
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="content">
        {/* Page Header */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Sendungsverfolgung</h1>
            <p className="subtitle">
              Verfolgen Sie Kaffeesendungen von Peru nach Deutschland und Europa
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
            <button type="button" className="btn" onClick={() => refetch()}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
                <path d="M16 21h5v-5"/>
              </svg>
              Aktualisieren
            </button>
            <button
              type="button"
              className="btn btnPrimary"
              onClick={() => setShowCreateModal(true)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Neue Sendung
            </button>
          </div>
        </header>

        {/* KPI Grid */}
        <div className="kpiGrid">
          <div className="kpiCard">
            <span className="cardLabel">Sendungen Gesamt</span>
            <span className="cardValue">{stats.total}</span>
            <span className="cardHint">Alle Zeiten</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">In Transit</span>
            <span className="cardValue">{stats.inTransit}</span>
            <span className="cardHint">Aktuell unterwegs</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Angekommen</span>
            <span className="cardValue">{stats.arrived}</span>
            <span className="cardHint">Abgeschlossene Lieferungen</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Gesamtgewicht</span>
            <span className="cardValue">
              {stats.totalWeight > 1000 
                ? `${(stats.totalWeight / 1000).toFixed(1)}t`
                : `${stats.totalWeight}kg`}
            </span>
            <span className="cardHint">Kaffee verschifft</span>
          </div>
        </div>

        {/* Arriving Soon Alert */}
        {arrivingSoon.length > 0 && (
          <div className="panel" style={{ marginBottom: "var(--space-6)" }}>
            <div className="panelHeader">
              <h2 className="panelTitle">Bald ankommend</h2>
              <span className="badge badgeWarn">{arrivingSoon.length} Sendungen</span>
            </div>
            <div className="panelBody">
              <div className="shipmentCards">
                {arrivingSoon.map((shipment) => {
                  const eta = shipment.estimated_arrival || shipment.eta;
                  if (!eta) return null;
                  const daysUntilArrival = differenceInDays(new Date(eta), new Date());
                  return (
                    <div key={shipment.id} className="shipmentCard arriving">
                      <div className="shipmentCardHeader">
                        <span className="shipmentCardTitle">
                          {shipment.container_number || `ID-${shipment.id}`}
                        </span>
                        <span className="badge badgeWarn">
                          {daysUntilArrival === 0 ? "Heute" : `${daysUntilArrival} Tage`}
                        </span>
                      </div>
                      <p className="shipmentCardRoute">
                        {shipment.origin_port} - {shipment.destination_port}
                      </p>
                      <span className="shipmentCardEta">
                        ETA: {format(new Date(eta), "dd.MM.yyyy")}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Active Shipments */}
        {activeShipments.filter((s) => s.status === "in_transit").length > 0 && (
          <div className="panel" style={{ marginBottom: "var(--space-6)" }}>
            <div className="panelHeader">
              <h2 className="panelTitle">Aktive Sendungen</h2>
              <span className="badge badgeInfo">
                {activeShipments.filter((s) => s.status === "in_transit").length} in Transit
              </span>
            </div>
            <div className="panelBody">
              <div className="shipmentCards">
                {activeShipments
                  .filter((s) => s.status === "in_transit")
                  .map((shipment) => {
                    const progress = calculateProgress(shipment);
                    const eta = shipment.estimated_arrival || shipment.eta;
                    const statusBadge = getStatusBadge(shipment.status);

                    return (
                      <div key={shipment.id} className="shipmentCard">
                        <div className="shipmentCardHeader">
                          <div>
                            <span className="shipmentCardTitle">
                              {shipment.container_number || `ID-${shipment.id}`}
                            </span>
                            <span className="shipmentCardCarrier">
                              {shipment.carrier || "Carrier"}
                            </span>
                          </div>
                          <span className={`badge ${statusBadge.className}`}>
                            {statusBadge.label}
                          </span>
                        </div>

                        <p className="shipmentCardRoute">
                          {shipment.origin_port} - {shipment.destination_port}
                        </p>
                        
                        {shipment.current_location && (
                          <p className="shipmentCardLocation">
                            Aktuell: {shipment.current_location}
                          </p>
                        )}

                        <div className="shipmentProgress">
                          <div className="shipmentProgressHeader">
                            <span>Fortschritt</span>
                            <span>{Math.round(progress)}%</span>
                          </div>
                          <div className="shipmentProgressBar">
                            <div 
                              className="shipmentProgressFill" 
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                        </div>

                        <div className="shipmentCardDates">
                          <div>
                            <span className="shipmentCardDateLabel">Abfahrt</span>
                            <span className="shipmentCardDateValue">
                              {shipment.departure_date
                                ? format(new Date(shipment.departure_date), "dd.MM.")
                                : "-"}
                            </span>
                          </div>
                          <div>
                            <span className="shipmentCardDateLabel">ETA</span>
                            <span className="shipmentCardDateValue">
                              {eta ? format(new Date(eta), "dd.MM.") : "-"}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>
        )}

        {/* All Shipments Table */}
        <div className="panel">
          <div className="panelHeader">
            <h2 className="panelTitle">Alle Sendungen</h2>
            <span className="badge">{shipments.length} Eintraege</span>
          </div>

          {shipments.length > 0 ? (
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Referenz</th>
                    <th>Route</th>
                    <th>Spediteur</th>
                    <th>Lots</th>
                    <th>Gewicht</th>
                    <th>Abfahrt</th>
                    <th>ETA / Ankunft</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {shipments.map((shipment) => {
                    const statusBadge = getStatusBadge(shipment.status);
                    const eta = shipment.estimated_arrival || shipment.eta;
                    return (
                      <tr key={shipment.id}>
                        <td>
                          <span style={{ fontWeight: 600, fontFamily: "var(--font-mono)", fontSize: "var(--font-size-sm)" }}>
                            {shipment.container_number || `ID-${shipment.id}`}
                          </span>
                        </td>
                        <td>
                          <span className="small">
                            {shipment.origin_port} - {shipment.destination_port}
                          </span>
                        </td>
                        <td>{shipment.carrier || "-"}</td>
                        <td>
                          <span className="badge">
                            {shipment.lot_ids?.length ?? (shipment.lot_id ? 1 : 0)}
                          </span>
                        </td>
                        <td>
                          {shipment.weight_kg 
                            ? `${(shipment.weight_kg / 1000).toFixed(1)}t`
                            : "-"}
                        </td>
                        <td>
                          {shipment.departure_date
                            ? format(new Date(shipment.departure_date), "dd.MM.yy")
                            : "-"}
                        </td>
                        <td>
                          {shipment.actual_arrival
                            ? format(new Date(shipment.actual_arrival), "dd.MM.yy")
                            : eta
                              ? format(new Date(eta), "dd.MM.yy")
                              : "-"}
                        </td>
                        <td>
                          {shipment.deleted_at ? (
                            <span className="badge badgeWarn">Archiviert</span>
                          ) : (
                            <span className={`badge ${statusBadge.className}`}>
                              {statusBadge.label}
                            </span>
                          )}
                        </td>
                        <td>
                          <div className="tableActions">
                            {shipment.deleted_at ? (
                              <button
                                className="btn btnSm"
                                onClick={() => restoreShipment(shipment.id)}
                              >
                                Wiederherstellen
                              </button>
                            ) : (
                              <button
                                className="btn btnSm btnDanger"
                                onClick={() => archiveShipment(shipment.id)}
                              >
                                Archivieren
                              </button>
                            )}
                          </div>
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
                  <rect x="1" y="3" width="15" height="13" rx="1"/>
                  <path d="M16 8h4l3 3v5h-7V8z"/>
                  <circle cx="5.5" cy="18.5" r="2.5"/>
                  <circle cx="18.5" cy="18.5" r="2.5"/>
                </svg>
                <h3 className="h4">Keine Sendungen vorhanden</h3>
                <p className="subtitle">
                  Erstellen Sie Ihre erste Sendung, um mit dem Tracking zu beginnen.
                </p>
                <button
                  type="button"
                  className="btn btnPrimary"
                  onClick={() => setShowCreateModal(true)}
                  style={{ marginTop: "var(--space-4)" }}
                >
                  Erste Sendung erstellen
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="modalOverlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modalHeader">
              <h2 className="h2">Neue Sendung erstellen</h2>
              <button
                type="button"
                className="btn btnSm btnGhost"
                onClick={() => setShowCreateModal(false)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreateSubmit}>
              <div className="modalBody">
                <div className="fieldGrid2">
                  <div className="field">
                    <label className="fieldLabel">Container-Nummer *</label>
                    <input
                      type="text"
                      className="input"
                      value={createForm.container_number}
                      onChange={(e) => setCreateForm({ ...createForm, container_number: e.target.value })}
                      required
                      minLength={5}
                      maxLength={50}
                      placeholder="MSCU1234567"
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Bill of Lading *</label>
                    <input
                      type="text"
                      className="input"
                      value={createForm.bill_of_lading}
                      onChange={(e) => setCreateForm({ ...createForm, bill_of_lading: e.target.value })}
                      required
                      minLength={3}
                      maxLength={100}
                      placeholder="BOL-2024-001"
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Gewicht (kg) *</label>
                    <input
                      type="number"
                      className="input"
                      value={createForm.weight_kg}
                      onChange={(e) => setCreateForm({ ...createForm, weight_kg: Number(e.target.value) })}
                      required
                      min={1}
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Container-Typ *</label>
                    <select
                      className="input"
                      value={createForm.container_type}
                      onChange={(e) => setCreateForm({ ...createForm, container_type: e.target.value })}
                      required
                    >
                      <option value="20ft">20ft</option>
                      <option value="40ft">40ft</option>
                      <option value="40ft_hc">40ft HC</option>
                    </select>
                  </div>
                </div>

                <div className="field">
                  <label className="fieldLabel">Ursprungshafen *</label>
                  <input
                    type="text"
                    className="input"
                    value={createForm.origin_port}
                    onChange={(e) => setCreateForm({ ...createForm, origin_port: e.target.value })}
                    required
                    maxLength={100}
                  />
                </div>

                <div className="field">
                  <label className="fieldLabel">Zielhafen *</label>
                  <input
                    type="text"
                    className="input"
                    value={createForm.destination_port}
                    onChange={(e) => setCreateForm({ ...createForm, destination_port: e.target.value })}
                    required
                    maxLength={100}
                  />
                </div>

                <div className="fieldGrid2">
                  <div className="field">
                    <label className="fieldLabel">Abfahrtsdatum</label>
                    <input
                      type="date"
                      className="input"
                      value={createForm.departure_date}
                      onChange={(e) => setCreateForm({ ...createForm, departure_date: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Voraussichtliche Ankunft</label>
                    <input
                      type="date"
                      className="input"
                      value={createForm.estimated_arrival}
                      onChange={(e) => setCreateForm({ ...createForm, estimated_arrival: e.target.value })}
                    />
                  </div>
                </div>

                <div className="field">
                  <label className="fieldLabel">Lot-IDs (optional)</label>
                  <input
                    type="text"
                    className="input"
                    value={createForm.lot_ids}
                    onChange={(e) => setCreateForm({ ...createForm, lot_ids: e.target.value })}
                    placeholder="101, 102, 103"
                  />
                  <span className="fieldHint">Kommasepariert</span>
                </div>

                <div className="field">
                  <label className="fieldLabel">Notizen</label>
                  <textarea
                    className="input"
                    value={createForm.notes}
                    onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                    rows={3}
                    maxLength={2000}
                  />
                </div>
              </div>

              <div className="modalFooter">
                <button type="button" className="btn" onClick={() => setShowCreateModal(false)}>
                  Abbrechen
                </button>
                <button type="submit" className="btn btnPrimary" disabled={createShipment.isPending}>
                  {createShipment.isPending ? "Erstellen..." : "Sendung erstellen"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <style jsx>{`
        .shipmentCards {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: var(--space-4);
        }
        .shipmentCard {
          padding: var(--space-4);
          background: var(--color-bg-subtle);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
        }
        .shipmentCard.arriving {
          background: var(--color-warning-subtle);
          border-color: var(--color-warning-border);
        }
        .shipmentCardHeader {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: var(--space-3);
        }
        .shipmentCardTitle {
          font-weight: var(--font-weight-semibold);
          font-size: var(--font-size-base);
          display: block;
        }
        .shipmentCardCarrier {
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
        }
        .shipmentCardRoute {
          font-size: var(--font-size-sm);
          color: var(--color-text-secondary);
          margin: 0 0 var(--space-2);
        }
        .shipmentCardLocation {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          margin: 0 0 var(--space-3);
        }
        .shipmentCardEta {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }
        .shipmentProgress {
          margin-bottom: var(--space-3);
        }
        .shipmentProgressHeader {
          display: flex;
          justify-content: space-between;
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          margin-bottom: var(--space-2);
        }
        .shipmentProgressBar {
          width: 100%;
          height: 6px;
          background: var(--color-border);
          border-radius: var(--radius-full);
          overflow: hidden;
        }
        .shipmentProgressFill {
          height: 100%;
          background: var(--color-accent);
          transition: width 300ms ease;
        }
        .shipmentCardDates {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-3);
          padding-top: var(--space-3);
          border-top: 1px solid var(--color-border);
        }
        .shipmentCardDateLabel {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          display: block;
        }
        .shipmentCardDateValue {
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-semibold);
        }
        .modalOverlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: var(--space-4);
        }
        .modal {
          width: 100%;
          max-width: 600px;
          background: var(--color-surface);
          border-radius: var(--radius-xl);
          box-shadow: var(--shadow-xl);
          max-height: 90vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }
        .modalHeader {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--space-5);
          border-bottom: 1px solid var(--color-border);
        }
        .modalBody {
          padding: var(--space-5);
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }
        .modalFooter {
          display: flex;
          justify-content: flex-end;
          gap: var(--space-3);
          padding: var(--space-4) var(--space-5);
          border-top: 1px solid var(--color-border);
          background: var(--color-bg-subtle);
        }
      `}</style>
    </div>
  );
}
