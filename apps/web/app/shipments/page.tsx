"use client";

import React, { useState, useEffect } from "react";
import { format, differenceInDays } from "date-fns";
import { useShipments, useCreateShipment } from "../hooks/useShipments";
import { Shipment } from "../types";

export default function ShipmentsDashboard() {
  const [showCreateModal, setShowCreateModal] = useState(false);
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
  });

  const { data: shipmentsResponse, isLoading, error } = useShipments({ limit: 200 });
  const createShipment = useCreateShipment();
  const [now, setNow] = useState(0);
  useEffect(() => setNow(Date.now()), []);
  
  const shipments = shipmentsResponse?.items || [];

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createShipment.mutateAsync({
        ...createForm,
        weight_kg: Number(createForm.weight_kg),
        departure_date: createForm.departure_date || null,
        estimated_arrival: createForm.estimated_arrival || null,
        notes: createForm.notes || null,
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
      });
    } catch (error) {
      console.error("Failed to create shipment:", error);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="page">
        <div className="pageHeader">
          <div className="h1">Sendungsverfolgung</div>
        </div>
        <div className="panel" style={{ padding: "40px", textAlign: "center" }}>
          <div>Laden...</div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="page">
        <div className="pageHeader">
          <div className="h1">Sendungsverfolgung</div>
        </div>
        <div className="panel" style={{ padding: "40px", textAlign: "center", color: "var(--danger)" }}>
          <div>Fehler beim Laden der Sendungen</div>
          <div style={{ fontSize: "14px", marginTop: "8px" }}>{String(error)}</div>
        </div>
      </div>
    );
  }

  // Calculate stats
  const stats = {
    total: shipments.length,
    inTransit: shipments.filter((s) => s.status === "in_transit").length,
    arrived: shipments.filter((s) => s.status === "delivered" || s.status === "arrived").length,
    totalWeight: shipments.reduce((sum, s) => sum + (s.weight_kg || 0), 0),
  };

  // Calculate progress from dates
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

  // Shipments arriving soon (within 7 days)
  const arrivingSoon = shipments.filter((s) => {
    const eta = s.estimated_arrival || s.eta;
    if (s.status !== "in_transit" || !eta) return false;
    const daysUntilArrival = differenceInDays(new Date(eta), new Date());
    return daysUntilArrival >= 0 && daysUntilArrival <= 7;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "in_transit":
        return { bg: "rgba(87,134,255,0.12)", border: "rgba(87,134,255,0.35)" };
      case "arrived":
        return { bg: "rgba(64,214,123,0.12)", border: "rgba(64,214,123,0.35)" };
      case "delayed":
        return { bg: "rgba(255,183,64,0.12)", border: "rgba(255,183,64,0.35)" };
      default:
        return { bg: "rgba(255,255,255,0.02)", border: "var(--border)" };
    }
  };

  // Empty state
  if (shipments.length === 0) {
    return (
      <div className="page">
        <div className="pageHeader">
          <div>
            <div className="h1">Sendungsverfolgung</div>
            <div className="muted">
              Verfolgen Sie Kaffeesendungen von Peru nach Deutschland und Europa
            </div>
          </div>
          <div className="actions">
            <button 
              type="button" 
              className="btn btnPrimary"
              onClick={() => setShowCreateModal(true)}
            >
              Sendung hinzufügen
            </button>
          </div>
        </div>
        <div style={{ padding: "60px 40px", textAlign: "center" }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>📦</div>
          <div style={{ fontSize: "18px", fontWeight: "600", marginBottom: "8px" }}>
            Keine Sendungen vorhanden
          </div>
          <div style={{ fontSize: "14px", color: "var(--muted)", marginBottom: "20px" }}>
            Erstellen Sie Ihre erste Sendung, um mit dem Tracking zu beginnen
          </div>
          <button 
            type="button" 
            className="btn btnPrimary"
            onClick={() => setShowCreateModal(true)}
          >
            Erste Sendung erstellen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Sendungsverfolgung</div>
          <div className="muted">
            Verfolgen Sie Kaffeesendungen von Peru nach Deutschland und Europa
          </div>
        </div>
        <div className="actions">
          <button 
            type="button" 
            className="btn btnPrimary"
            onClick={() => setShowCreateModal(true)}
          >
            Sendung hinzufügen
          </button>
        </div>
      </div>

      {/* Overview KPIs */}
      <div className="grid gridCols4" style={{ marginBottom: "18px" }}>
        <div className="panel card">
          <div className="cardLabel">Sendungen gesamt</div>
          <div className="cardValue">{stats.total}</div>
          <div className="cardHint">Alle Zeiten</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">In Transit</div>
          <div className="cardValue">{stats.inTransit}</div>
          <div className="cardHint">Aktuell im Versand</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Angekommen</div>
          <div className="cardValue">{stats.arrived}</div>
          <div className="cardHint">Abgeschlossene Lieferungen</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Gesamtgewicht</div>
          <div className="cardValue">{(stats.totalWeight / 1000).toFixed(1)}t</div>
          <div className="cardHint">Kaffee verschifft</div>
        </div>
      </div>

      {/* Arriving Soon Widget */}
      {arrivingSoon.length > 0 && (
        <div className="panel" style={{ padding: "18px", marginBottom: "18px" }}>
          <div className="h2">Bald ankommend</div>
          <div className="muted" style={{ marginBottom: "14px" }}>
            Sendungen, die innerhalb von 7 Tagen ankommen
          </div>
          <div className="grid gridCols3" style={{ gap: "12px" }}>
            {arrivingSoon.map((shipment) => {
              const eta = shipment.estimated_arrival || shipment.eta;
              if (!eta) return null; // Extra safety check
              const daysUntilArrival = differenceInDays(new Date(eta), new Date());
              return (
                <div
                  key={shipment.id}
                  className="panel"
                  style={{
                    padding: "14px",
                    background: "rgba(255,183,64,0.08)",
                    border: "1px solid rgba(255,183,64,0.25)",
                  }}
                >
                  <div style={{ fontWeight: "700", marginBottom: "6px" }}>
                    {shipment.container_number || `ID-${shipment.id}`}
                  </div>
                  <div style={{ fontSize: "13px", color: "var(--muted)", marginBottom: "8px" }}>
                    {shipment.origin_port} → {shipment.destination_port}
                  </div>
                  <div style={{ fontSize: "20px", fontWeight: "800", marginBottom: "4px" }}>
                    {daysUntilArrival} Tage
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--muted)" }}>
                    ETA: {format(new Date(eta), "dd. MMM yyyy")}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Active Shipments Cards */}
      <div className="panel" style={{ padding: "18px", marginBottom: "18px" }}>
        <div className="h2">Aktive Sendungen</div>
        <div className="muted" style={{ marginBottom: "14px" }}>
          Aktuell in Transit
        </div>
        <div className="grid gridCols2" style={{ gap: "14px" }}>
          {shipments
            .filter((s) => s.status === "in_transit")
            .map((shipment) => {
              const statusColors = getStatusColor(shipment.status);
              const progress = calculateProgress(shipment);
              const eta = shipment.estimated_arrival || shipment.eta;
              
              return (
                <div
                  key={shipment.id}
                  className="panel"
                  style={{
                    padding: "18px",
                    background: statusColors.bg,
                    border: `1px solid ${statusColors.border}`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "12px" }}>
                    <div>
                      <div style={{ fontWeight: "700", fontSize: "16px", marginBottom: "4px" }}>
                        {shipment.container_number || `ID-${shipment.id}`}
                      </div>
                      <div style={{ fontSize: "13px", color: "var(--muted)" }}>
                        {shipment.carrier || "Carrier"}
                      </div>
                    </div>
                    <span className="badge" style={{ background: statusColors.bg, borderColor: statusColors.border }}>
                      {shipment.status.replace("_", " ")}
                    </span>
                  </div>

                  <div style={{ marginBottom: "12px" }}>
                    <div style={{ fontSize: "14px", marginBottom: "4px" }}>
                      <strong>Route:</strong> {shipment.origin_port} → {shipment.destination_port}
                    </div>
                    <div style={{ fontSize: "13px", color: "var(--muted)" }}>
                      {shipment.current_location || "In Transit"}
                    </div>
                  </div>

                  <div style={{ marginBottom: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px" }}>
                      <span>Fortschritt</span>
                      <span>{Math.round(progress)}%</span>
                    </div>
                    <div style={{ width: "100%", height: "6px", background: "rgba(0,0,0,0.2)", borderRadius: "999px", overflow: "hidden" }}>
                      <div
                        style={{
                          width: `${progress}%`,
                          height: "100%",
                          background: "rgba(200,149,108,0.8)",
                          transition: "width 0.3s ease",
                        }}
                      />
                    </div>
                  </div>

                  <div className="grid gridCols2" style={{ gap: "10px", fontSize: "12px" }}>
                    <div>
                      <div style={{ color: "var(--muted)" }}>Abfahrt</div>
                      <div style={{ fontWeight: "600" }}>
                        {shipment.departure_date ? format(new Date(shipment.departure_date), "dd. MMM") : "–"}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: "var(--muted)" }}>ETA</div>
                      <div style={{ fontWeight: "600" }}>
                        {eta ? format(new Date(eta), "dd. MMM") : "–"}
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid var(--border)" }}>
                    <button 
                      type="button" 
                      className="btn" 
                      style={{ width: "100%", fontSize: "12px" }}
                      onClick={() => alert(`Shipment details page coming soon (ID: ${shipment.id})`)}
                    >
                      Details anzeigen →
                    </button>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* All Shipments Table */}
      <div className="panel" style={{ padding: "18px" }}>
        <div className="h2">Alle Sendungen</div>
        <div className="muted" style={{ marginBottom: "14px" }}>
          Vollständiger Sendungsverlauf
        </div>

        <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Referenz</th>
                <th>Route</th>
                <th>Spediteur</th>
                <th>Container</th>
                <th>Gewicht (kg)</th>
                <th>Abfahrt</th>
                <th>ETA / Ankunft</th>
                <th>Status</th>
                <th>Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {shipments.map((shipment) => {
                const statusColors = getStatusColor(shipment.status);
                const eta = shipment.estimated_arrival || shipment.eta;
                return (
                  <tr key={shipment.id}>
                    <td style={{ fontWeight: "600" }}>{shipment.container_number || `ID-${shipment.id}`}</td>
                    <td>
                      {shipment.origin_port} → {shipment.destination_port}
                    </td>
                    <td>{shipment.carrier || "–"}</td>
                    <td className="mono" style={{ fontSize: "12px" }}>
                      {shipment.container_number || "–"}
                    </td>
                    <td>{shipment.weight_kg ? shipment.weight_kg.toLocaleString() : "–"}</td>
                    <td>{shipment.departure_date ? format(new Date(shipment.departure_date), "MMM dd, yyyy") : "–"}</td>
                    <td>
                      {shipment.actual_arrival
                        ? format(new Date(shipment.actual_arrival), "MMM dd, yyyy")
                        : eta
                        ? format(new Date(eta), "MMM dd, yyyy")
                        : "–"}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: statusColors.bg,
                          borderColor: statusColors.border,
                        }}
                      >
                        {shipment.status.replace("_", " ")}
                      </span>
                    </td>
                    <td>
                      <button 
                        type="button" 
                        className="link"
                        style={{ background: "none", border: "none", padding: 0, cursor: "pointer" }}
                        onClick={() => alert(`Shipment details page coming soon (ID: ${shipment.id})`)}
                      >
                        Details →
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Shipment Modal */}
      {showCreateModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="panel"
            style={{ 
              width: "90%", 
              maxWidth: "600px", 
              padding: "24px",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <h2 style={{ margin: 0 }}>Neue Sendung erstellen</h2>
              <button
                type="button"
                className="btn"
                onClick={() => setShowCreateModal(false)}
                style={{ padding: "4px 12px" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubmit}>
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                  Container-Nummer *
                </label>
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

              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                  Bill of Lading *
                </label>
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

              <div className="grid gridCols2" style={{ gap: "16px", marginBottom: "16px" }}>
                <div>
                  <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                    Gewicht (kg) *
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={createForm.weight_kg}
                    onChange={(e) => setCreateForm({ ...createForm, weight_kg: Number(e.target.value) })}
                    required
                    min={1}
                  />
                </div>
                <div>
                  <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                    Container-Typ *
                  </label>
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

              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                  Ursprungshafen *
                </label>
                <input
                  type="text"
                  className="input"
                  value={createForm.origin_port}
                  onChange={(e) => setCreateForm({ ...createForm, origin_port: e.target.value })}
                  required
                  maxLength={100}
                />
              </div>

              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                  Zielhafen *
                </label>
                <input
                  type="text"
                  className="input"
                  value={createForm.destination_port}
                  onChange={(e) => setCreateForm({ ...createForm, destination_port: e.target.value })}
                  required
                  maxLength={100}
                />
              </div>

              <div className="grid gridCols2" style={{ gap: "16px", marginBottom: "16px" }}>
                <div>
                  <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                    Abfahrtsdatum
                  </label>
                  <input
                    type="date"
                    className="input"
                    value={createForm.departure_date}
                    onChange={(e) => setCreateForm({ ...createForm, departure_date: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                    Voraussichtliche Ankunft
                  </label>
                  <input
                    type="date"
                    className="input"
                    value={createForm.estimated_arrival}
                    onChange={(e) => setCreateForm({ ...createForm, estimated_arrival: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: "600" }}>
                  Notizen
                </label>
                <textarea
                  className="input"
                  value={createForm.notes}
                  onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                  rows={3}
                  maxLength={2000}
                />
              </div>

              <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="btn"
                  onClick={() => setShowCreateModal(false)}
                >
                  Abbrechen
                </button>
                <button
                  type="submit"
                  className="btn btnPrimary"
                  disabled={createShipment.isPending}
                >
                  {createShipment.isPending ? "Erstellen..." : "Sendung erstellen"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
