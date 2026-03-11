"use client";

import React, { useState, useMemo } from "react";
import { format, differenceInDays } from "date-fns";
import { useShipments, useCreateShipment } from "../hooks/useShipments";
import { apiFetch } from "../../lib/api";
import { Shipment } from "../types";
import KpiCard from "../components/KpiCard";
import StatusBadge from "../components/StatusBadge";
import ProgressBar from "../components/ProgressBar";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";

// ============================================================================
// Sub-Components
// ============================================================================

type ShipmentFormData = {
  container_number: string;
  bill_of_lading: string;
  weight_kg: number;
  container_type: string;
  origin_port: string;
  destination_port: string;
  departure_date: string;
  estimated_arrival: string;
  notes: string;
  lot_ids: string;
};

const createInitialShipmentForm = (): ShipmentFormData => ({
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

function ShipmentStats({ shipments }: { shipments: Shipment[] }) {
  const stats = useMemo(() => {
    const active = shipments.filter((s) => !s.deleted_at);
    return {
      total: active.length,
      inTransit: active.filter((s) => s.status === "in_transit").length,
      arrived: active.filter((s) => s.status === "delivered" || s.status === "arrived").length,
      totalWeight: active.reduce((sum, s) => sum + (s.weight_kg || 0), 0),
    };
  }, [shipments]);

  return (
    <div className="grid gridCols4" style={{ marginBottom: 18 }}>
      <KpiCard label="Sendungen gesamt" value={stats.total} hint="Alle Zeiten" />
      <KpiCard label="In Transit" value={stats.inTransit} hint="Aktuell im Versand" />
      <KpiCard label="Angekommen" value={stats.arrived} hint="Abgeschlossene Lieferungen" />
      <KpiCard
        label="Gesamtgewicht"
        value={`${(stats.totalWeight / 1000).toFixed(1)}t`}
        hint="Kaffee verschifft"
      />
    </div>
  );
}

function ArrivingSoonWidget({ shipments }: { shipments: Shipment[] }) {
  const arrivingSoon = useMemo(() => {
    return shipments.filter((s) => {
      if (s.deleted_at) return false;
      const eta = s.estimated_arrival || s.eta;
      if (s.status !== "in_transit" || !eta) return false;
      const daysUntilArrival = differenceInDays(new Date(eta), new Date());
      return daysUntilArrival >= 0 && daysUntilArrival <= 7;
    });
  }, [shipments]);

  if (arrivingSoon.length === 0) return null;

  return (
    <div className="panel" style={{ marginBottom: 18 }}>
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Bald ankommend</div>
          <div className="muted small">Sendungen, die innerhalb von 7 Tagen ankommen</div>
        </div>
        <span className="badge badgeWarn">{arrivingSoon.length}</span>
      </div>
      <div className="panelBody">
        <div className="grid gridCols3" style={{ gap: 12 }}>
          {arrivingSoon.map((shipment) => {
            const eta = shipment.estimated_arrival || shipment.eta;
            if (!eta) return null;
            const daysUntilArrival = differenceInDays(new Date(eta), new Date());
            return (
              <div
                key={shipment.id}
                className="panel"
                style={{
                  padding: 14,
                  background: "rgba(255, 183, 64, 0.08)",
                  border: "1px solid rgba(255, 183, 64, 0.25)",
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: 6 }}>
                  {shipment.container_number || `ID-${shipment.id}`}
                </div>
                <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 8 }}>
                  {shipment.origin_port} → {shipment.destination_port}
                </div>
                <div style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>
                  {daysUntilArrival === 0 ? "Heute" : `${daysUntilArrival} Tage`}
                </div>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>
                  ETA: {format(new Date(eta), "dd. MMM yyyy")}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ActiveShipmentCard({
  shipment,
  now,
  onViewDetails,
}: {
  shipment: Shipment;
  now: number;
  onViewDetails: (id: number) => void;
}) {
  const progress = useMemo(() => {
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
  }, [shipment, now]);

  const eta = shipment.estimated_arrival || shipment.eta;

  return (
    <div
      className="panel"
      style={{
        padding: 18,
        background: "rgba(87, 134, 255, 0.08)",
        border: "1px solid rgba(87, 134, 255, 0.25)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "start",
          marginBottom: 12,
        }}
      >
        <div>
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>
            {shipment.container_number || `ID-${shipment.id}`}
          </div>
          <div style={{ fontSize: 13, color: "var(--muted)" }}>
            {shipment.carrier || "Carrier nicht angegeben"}
          </div>
        </div>
        <StatusBadge status={shipment.status} />
      </div>

      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 14, marginBottom: 4 }}>
          <strong>Route:</strong> {shipment.origin_port} → {shipment.destination_port}
        </div>
        <div style={{ fontSize: 13, color: "var(--muted)" }}>
          {shipment.current_location || "Position unbekannt"}
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <ProgressBar value={progress} />
      </div>

      <div className="grid gridCols2" style={{ gap: 10, fontSize: 12, marginBottom: 16 }}>
        <div>
          <div style={{ color: "var(--muted)", marginBottom: 2 }}>Abfahrt</div>
          <div style={{ fontWeight: 600 }}>
            {shipment.departure_date
              ? format(new Date(shipment.departure_date), "dd. MMM yyyy")
              : "-"}
          </div>
        </div>
        <div>
          <div style={{ color: "var(--muted)", marginBottom: 2 }}>ETA</div>
          <div style={{ fontWeight: 600 }}>
            {eta ? format(new Date(eta), "dd. MMM yyyy") : "-"}
          </div>
        </div>
      </div>

      <button
        type="button"
        className="btn btnFull"
        style={{ fontSize: 13 }}
        onClick={() => onViewDetails(shipment.id)}
      >
        Details anzeigen
      </button>
    </div>
  );
}

function ShipmentTable({
  shipments,
  onArchive,
  onRestore,
  onViewDetails,
}: {
  shipments: Shipment[];
  onArchive: (id: number) => void;
  onRestore: (id: number) => void;
  onViewDetails: (id: number) => void;
}) {
  return (
    <div className="panel" style={{ marginBottom: 18 }}>
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Alle Sendungen</div>
          <div className="muted small">Vollstaendiger Sendungsverlauf</div>
        </div>
        <span className="badge">{shipments.length} Eintraege</span>
      </div>
      <div style={{ overflowX: "auto" }}>
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
              <th style={{ width: 140 }}>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {shipments.map((shipment) => {
              const eta = shipment.estimated_arrival || shipment.eta;
              const lotsCount = shipment.lot_ids?.length ?? (shipment.lot_id ? 1 : 0);
              return (
                <tr key={shipment.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>
                      {shipment.container_number || `ID-${shipment.id}`}
                    </div>
                    {shipment.bill_of_lading && (
                      <div className="mono small muted">{shipment.bill_of_lading}</div>
                    )}
                  </td>
                  <td>
                    <div>{shipment.origin_port}</div>
                    <div className="muted small">→ {shipment.destination_port}</div>
                  </td>
                  <td>{shipment.carrier || "-"}</td>
                  <td>
                    {lotsCount > 0 ? (
                      <span className="badge">{lotsCount} Lots</span>
                    ) : (
                      <span className="muted">-</span>
                    )}
                  </td>
                  <td>
                    {shipment.weight_kg ? (
                      <span className="mono">{shipment.weight_kg.toLocaleString()} kg</span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td>
                    {shipment.departure_date
                      ? format(new Date(shipment.departure_date), "dd.MM.yyyy")
                      : "-"}
                  </td>
                  <td>
                    {shipment.actual_arrival
                      ? format(new Date(shipment.actual_arrival), "dd.MM.yyyy")
                      : eta
                        ? format(new Date(eta), "dd.MM.yyyy")
                        : "-"}
                  </td>
                  <td>
                    <StatusBadge status={shipment.status} isArchived={!!shipment.deleted_at} />
                  </td>
                  <td>
                    <div className="row" style={{ gap: 8 }}>
                      <button
                        type="button"
                        className="link small"
                        onClick={() => onViewDetails(shipment.id)}
                      >
                        Details
                      </button>
                      {shipment.deleted_at ? (
                        <button
                          type="button"
                          className="link small"
                          onClick={() => onRestore(shipment.id)}
                        >
                          Restore
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="link small"
                          style={{ color: "var(--accent-3)" }}
                          onClick={() => onArchive(shipment.id)}
                        >
                          Archiv
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
    </div>
  );
}

function CreateShipmentModal({
  isOpen,
  onClose,
  onSubmit,
  isPending,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ShipmentFormData) => void;
  isPending: boolean;
}) {
  const [form, setForm] = useState<ShipmentFormData>(createInitialShipmentForm);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  const updateField = (field: string, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "rgba(0, 0, 0, 0.6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        backdropFilter: "blur(4px)",
      }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="panel"
        style={{
          width: "90%",
          maxWidth: 600,
          padding: 24,
          maxHeight: "90vh",
          overflowY: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          <h2 style={{ margin: 0, fontFamily: "var(--display)" }}>Neue Sendung erstellen</h2>
          <button type="button" className="btn" onClick={onClose} style={{ padding: "6px 12px" }}>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="formGrid" style={{ marginBottom: 16 }}>
            <div className="field">
              <label className="fieldLabel">Container-Nummer *</label>
              <input
                type="text"
                className="input"
                value={form.container_number}
                onChange={(e) => updateField("container_number", e.target.value)}
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
                value={form.bill_of_lading}
                onChange={(e) => updateField("bill_of_lading", e.target.value)}
                required
                minLength={3}
                maxLength={100}
                placeholder="BOL-2024-001"
              />
            </div>
          </div>

          <div className="formGrid" style={{ marginBottom: 16 }}>
            <div className="field">
              <label className="fieldLabel">Gewicht (kg) *</label>
              <input
                type="number"
                className="input"
                value={form.weight_kg}
                onChange={(e) => updateField("weight_kg", Number(e.target.value))}
                required
                min={1}
              />
            </div>
            <div className="field">
              <label className="fieldLabel">Container-Typ *</label>
              <select
                className="input"
                value={form.container_type}
                onChange={(e) => updateField("container_type", e.target.value)}
                required
              >
                <option value="20ft">20ft</option>
                <option value="40ft">40ft</option>
                <option value="40ft_hc">40ft HC</option>
              </select>
            </div>
          </div>

          <div className="formGrid" style={{ marginBottom: 16 }}>
            <div className="field">
              <label className="fieldLabel">Ursprungshafen *</label>
              <input
                type="text"
                className="input"
                value={form.origin_port}
                onChange={(e) => updateField("origin_port", e.target.value)}
                required
                maxLength={100}
              />
            </div>
            <div className="field">
              <label className="fieldLabel">Zielhafen *</label>
              <input
                type="text"
                className="input"
                value={form.destination_port}
                onChange={(e) => updateField("destination_port", e.target.value)}
                required
                maxLength={100}
              />
            </div>
          </div>

          <div className="formGrid" style={{ marginBottom: 16 }}>
            <div className="field">
              <label className="fieldLabel">Abfahrtsdatum</label>
              <input
                type="date"
                className="input"
                value={form.departure_date}
                onChange={(e) => updateField("departure_date", e.target.value)}
              />
            </div>
            <div className="field">
              <label className="fieldLabel">Voraussichtliche Ankunft</label>
              <input
                type="date"
                className="input"
                value={form.estimated_arrival}
                onChange={(e) => updateField("estimated_arrival", e.target.value)}
              />
            </div>
          </div>

          <div className="field" style={{ marginBottom: 16 }}>
            <label className="fieldLabel">Lot-IDs (optional, kommasepariert)</label>
            <input
              type="text"
              className="input"
              value={form.lot_ids}
              onChange={(e) => updateField("lot_ids", e.target.value)}
              placeholder="101, 102, 103"
            />
          </div>

          <div className="field" style={{ marginBottom: 20 }}>
            <label className="fieldLabel">Notizen</label>
            <textarea
              className="input"
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              rows={3}
              maxLength={2000}
              placeholder="Optionale Anmerkungen zur Sendung..."
            />
          </div>

          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
            <button type="button" className="btn" onClick={onClose}>
              Abbrechen
            </button>
            <button type="submit" className="btn btnPrimary" disabled={isPending}>
              {isPending ? "Erstellen..." : "Sendung erstellen"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function ShipmentsDashboard() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createModalKey, setCreateModalKey] = useState(0);
  const [showArchived, setShowArchived] = useState(false);
  const [now] = useState(() => Date.now());

  const { data: shipmentsResponse, isLoading, error, refetch } = useShipments({
    limit: 200,
    include_deleted: showArchived,
  });
  const createShipment = useCreateShipment();

  const shipments = shipmentsResponse?.items ?? [];
  const activeShipments = shipments.filter((s) => !s.deleted_at);
  const inTransitShipments = activeShipments.filter((s) => s.status === "in_transit");

  const openCreateModal = () => {
    setCreateModalKey((prev) => prev + 1);
    setShowCreateModal(true);
  };

  const handleCreateSubmit = async (formData: ShipmentFormData) => {
    try {
      const parsedLotIds = formData.lot_ids
        ? formData.lot_ids
            .split(",")
            .map((v: string) => Number(v.trim()))
            .filter((v: number) => Number.isFinite(v) && v > 0)
        : null;
      const lotIds = parsedLotIds && parsedLotIds.length > 0 ? parsedLotIds : null;

      await createShipment.mutateAsync({
        ...formData,
        lot_id: null,
        cooperative_id: null,
        roaster_id: null,
        weight_kg: Number(formData.weight_kg),
        departure_date: formData.departure_date || null,
        estimated_arrival: formData.estimated_arrival || null,
        notes: formData.notes || null,
        lot_ids: lotIds,
      });
      setShowCreateModal(false);
      await refetch();
    } catch (createError) {
      console.error("Failed to create shipment:", createError);
    }
  };

  const archiveShipment = async (id: number) => {
    if (!confirm("Sendung archivieren?")) return;
    try {
      await apiFetch(`/shipments/${id}`, { method: "DELETE" });
      await refetch();
    } catch (archiveError) {
      console.error("Failed to archive shipment:", archiveError);
    }
  };

  const restoreShipment = async (id: number) => {
    try {
      await apiFetch(`/shipments/${id}/restore`, { method: "POST" });
      await refetch();
    } catch (restoreError) {
      console.error("Failed to restore shipment:", restoreError);
    }
  };

  const viewShipmentDetails = (id: number) => {
    alert(`Sendungsdetails fuer ID: ${id} (Detail-Seite in Entwicklung)`);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="page">
        <div className="pageHeader">
          <div>
            <div className="h1">Sendungsverfolgung</div>
            <div className="muted">Verfolgen Sie Kaffeesendungen von Peru nach Deutschland und Europa</div>
          </div>
        </div>
        <div className="panel">
          <LoadingState message="Sendungen werden geladen..." />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="page">
        <div className="pageHeader">
          <div>
            <div className="h1">Sendungsverfolgung</div>
            <div className="muted">Verfolgen Sie Kaffeesendungen von Peru nach Deutschland und Europa</div>
          </div>
        </div>
        <ErrorState
          title="Fehler beim Laden der Sendungen"
          message={String(error)}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  // Empty state
  if (shipments.length === 0) {
    return (
      <div className="page">
        <div className="pageHeader">
          <div>
            <div className="h1">Sendungsverfolgung</div>
            <div className="muted">Verfolgen Sie Kaffeesendungen von Peru nach Deutschland und Europa</div>
          </div>
          <div className="actions">
            <button type="button" className="btn btnPrimary" onClick={openCreateModal}>
              Sendung hinzufuegen
            </button>
          </div>
        </div>
        <div className="panel">
          <EmptyState
            title="Keine Sendungen vorhanden"
            description="Erstellen Sie Ihre erste Sendung, um mit dem Tracking zu beginnen"
            action={
              <button
                type="button"
                className="btn btnPrimary"
                onClick={openCreateModal}
              >
                Erste Sendung erstellen
              </button>
            }
          />
        </div>
        <CreateShipmentModal
          key={createModalKey}
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateSubmit}
          isPending={createShipment.isPending}
        />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Sendungsverfolgung</div>
          <div className="muted">Verfolgen Sie Kaffeesendungen von Peru nach Deutschland und Europa</div>
        </div>
        <div className="actions">
          <label className="row" style={{ gap: 6, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            <span className="small muted">Archivierte anzeigen</span>
          </label>
          <button type="button" className="btn btnPrimary" onClick={openCreateModal}>
            Sendung hinzufuegen
          </button>
        </div>
      </div>

      {/* KPI Summary */}
      <ShipmentStats shipments={shipments} />

      {/* Arriving Soon Widget */}
      <ArrivingSoonWidget shipments={shipments} />

      {/* Active Shipments Grid */}
      {inTransitShipments.length > 0 && (
        <div className="panel" style={{ marginBottom: 18 }}>
          <div className="panelHeader">
            <div>
              <div className="panelTitle">Aktive Sendungen</div>
              <div className="muted small">Aktuell in Transit</div>
            </div>
            <span className="badge statusInTransit">{inTransitShipments.length} aktiv</span>
          </div>
          <div className="panelBody">
            <div className="grid gridCols2" style={{ gap: 14 }}>
              {inTransitShipments.map((shipment) => (
                <ActiveShipmentCard
                  key={shipment.id}
                  shipment={shipment}
                  now={now}
                  onViewDetails={viewShipmentDetails}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Full History Table */}
      <ShipmentTable
        shipments={shipments}
        onArchive={archiveShipment}
        onRestore={restoreShipment}
        onViewDetails={viewShipmentDetails}
      />

      {/* Create Modal */}
      <CreateShipmentModal
        key={createModalKey}
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateSubmit}
        isPending={createShipment.isPending}
      />
    </div>
  );
}
