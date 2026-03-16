"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import { ErrorPanel } from "../components/AlertError";
import { toErrorMessage } from "../utils/error";

/* ============================================================
   LOTS MANAGEMENT - ENTERPRISE VIEW
   ============================================================ */

type Lot = {
  id: number;
  cooperative_id: number;
  name: string;
  crop_year: number | null;
  incoterm: string | null;
  price_per_kg: number | null;
  currency: string | null;
  weight_kg: number | null;
  expected_cupping_score: number | null;
  deleted_at: string | null;
};

type LotFormState = {
  cooperative_id: string;
  name: string;
  crop_year: string;
  incoterm: string;
  price_per_kg: string;
  currency: string;
  weight_kg: string;
  expected_cupping_score: string;
};

type CreateLotPayload = {
  cooperative_id: number;
  name: string;
  incoterm: string | null;
  currency: string | null;
  crop_year?: number;
  price_per_kg?: number;
  weight_kg?: number;
  expected_cupping_score?: number;
};

const INITIAL_FORM: LotFormState = {
  cooperative_id: "",
  name: "",
  crop_year: "",
  incoterm: "FOB",
  price_per_kg: "",
  currency: "USD",
  weight_kg: "",
  expected_cupping_score: "",
};

export default function LotsPage() {
  const [lots, setLots] = useState<Lot[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [form, setForm] = useState<LotFormState>(INITIAL_FORM);

  const load = useCallback(() => {
    return apiFetch<Lot[]>(`/lots?limit=200&include_deleted=${showArchived ? "true" : "false"}`)
      .then(setLots)
      .catch((error: unknown) => setErr(toErrorMessage(error)));
  }, [showArchived]);

  useEffect(() => {
    load();
  }, [load]);

  async function archiveLot(id: number) {
    if (!confirm("Lot archivieren?")) return;
    setBusyId(id);
    try {
      await apiFetch(`/lots/${id}`, { method: "DELETE" });
      load();
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  async function restoreLot(id: number) {
    setBusyId(id);
    try {
      await apiFetch(`/lots/${id}/restore`, { method: "POST" });
      load();
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  async function createLot() {
    setErr(null);
    setCreating(true);
    try {
      const payload: CreateLotPayload = {
        cooperative_id: Number(form.cooperative_id),
        name: String(form.name || "").trim(),
        incoterm: form.incoterm || null,
        currency: form.currency || null,
      };
      if (!payload.name) throw new Error("Name fehlt");
      if (!payload.cooperative_id) throw new Error("Kooperativen-ID fehlt");

      if (form.crop_year) payload.crop_year = Number(form.crop_year);
      if (form.price_per_kg) payload.price_per_kg = Number(form.price_per_kg);
      if (form.weight_kg) payload.weight_kg = Number(form.weight_kg);
      if (form.expected_cupping_score)
        payload.expected_cupping_score = Number(form.expected_cupping_score);

      await apiFetch<Lot>("/lots", { method: "POST", body: JSON.stringify(payload) });
      setForm(INITIAL_FORM);
      setShowForm(false);
      load();
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setCreating(false);
    }
  }

  // Stats
  const activeLots = lots.filter(l => !l.deleted_at);
  const stats = {
    total: activeLots.length,
    totalWeight: activeLots.reduce((sum, l) => sum + (l.weight_kg || 0), 0),
    avgScore: activeLots.filter(l => l.expected_cupping_score).length > 0
      ? activeLots.reduce((sum, l) => sum + (l.expected_cupping_score || 0), 0) / 
        activeLots.filter(l => l.expected_cupping_score).length
      : 0,
    currentYear: activeLots.filter(l => l.crop_year === new Date().getFullYear()).length,
  };

  return (
    <div className="page">
      <div className="content">
        {/* Page Header */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Kaffee Lots</h1>
            <p className="subtitle">
              Verwalten Sie Kaffeelots, Preise und Qualitaetsdaten
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
            <button 
              type="button" 
              className={`btn ${showForm ? "" : "btnPrimary"}`}
              onClick={() => setShowForm(!showForm)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              {showForm ? "Abbrechen" : "Neues Lot"}
            </button>
          </div>
        </header>

        {/* Error Display */}
        {err && (
          <ErrorPanel
            compact
            message={err}
            style={{ marginBottom: "var(--space-6)" }}
            onRetry={() => {
              setErr(null);
              void load();
            }}
          />
        )}

        {/* KPI Grid */}
        <div className="kpiGrid">
          <div className="kpiCard">
            <span className="cardLabel">Lots Gesamt</span>
            <span className="cardValue">{stats.total}</span>
            <span className="cardHint">Aktive Lots</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Gesamtgewicht</span>
            <span className="cardValue">
              {stats.totalWeight > 1000 
                ? `${(stats.totalWeight / 1000).toFixed(1)}t`
                : `${stats.totalWeight}kg`}
            </span>
            <span className="cardHint">verfügbare Menge</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Durchschn. Score</span>
            <span className="cardValue">{stats.avgScore > 0 ? stats.avgScore.toFixed(1) : "-"}</span>
            <span className="cardHint">Erwarteter SCA Score</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Aktuelle Ernte</span>
            <span className="cardValue">{stats.currentYear}</span>
            <span className="cardHint">Lots {new Date().getFullYear()}</span>
          </div>
        </div>

        {/* Create Form */}
        {showForm && (
          <div className="panel" style={{ marginBottom: "var(--space-6)" }}>
            <div className="panelHeader">
              <h2 className="panelTitle">Neues Lot anlegen</h2>
              <span className="badge badgeInfo">Formular</span>
            </div>
            <div className="panelBody">
              <div className="fieldGrid2">
                <div className="field">
                  <label className="fieldLabel">Kooperativen-ID *</label>
                  <input
                    type="number"
                    className="input"
                    placeholder="ID der Kooperative"
                    value={form.cooperative_id}
                    onChange={(e) => setForm({ ...form, cooperative_id: e.target.value })}
                  />
                  <span className="fieldHint">Finden Sie die ID in der Kooperativen-Liste</span>
                </div>
                <div className="field">
                  <label className="fieldLabel">Name *</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="z.B. Cajamarca Lot A"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </div>
                <div className="field">
                  <label className="fieldLabel">Erntejahr</label>
                  <input
                    type="number"
                    className="input"
                    placeholder={`z.B. ${new Date().getFullYear()}`}
                    value={form.crop_year}
                    onChange={(e) => setForm({ ...form, crop_year: e.target.value })}
                  />
                </div>
                <div className="field">
                  <label className="fieldLabel">Incoterm</label>
                  <select
                    className="input"
                    value={form.incoterm}
                    onChange={(e) => setForm({ ...form, incoterm: e.target.value })}
                  >
                    <option value="FOB">FOB</option>
                    <option value="CIF">CIF</option>
                    <option value="EXW">EXW</option>
                    <option value="FCA">FCA</option>
                  </select>
                </div>
                <div className="field">
                  <label className="fieldLabel">Preis/kg</label>
                  <input
                    type="number"
                    step="0.01"
                    className="input"
                    placeholder="z.B. 4.50"
                    value={form.price_per_kg}
                    onChange={(e) => setForm({ ...form, price_per_kg: e.target.value })}
                  />
                </div>
                <div className="field">
                  <label className="fieldLabel">Waehrung</label>
                  <select
                    className="input"
                    value={form.currency}
                    onChange={(e) => setForm({ ...form, currency: e.target.value })}
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="PEN">PEN</option>
                  </select>
                </div>
                <div className="field">
                  <label className="fieldLabel">Gewicht (kg)</label>
                  <input
                    type="number"
                    className="input"
                    placeholder="z.B. 5000"
                    value={form.weight_kg}
                    onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
                  />
                </div>
                <div className="field">
                  <label className="fieldLabel">Erwarteter SCA Score</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="100"
                    className="input"
                    placeholder="z.B. 85"
                    value={form.expected_cupping_score}
                    onChange={(e) => setForm({ ...form, expected_cupping_score: e.target.value })}
                  />
                </div>
              </div>
              <div className="btnGroup">
                <button
                  type="button"
                  className="btn btnPrimary"
                  onClick={createLot}
                  disabled={creating}
                >
                  {creating ? "Speichere..." : "Lot anlegen"}
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={() => {
                    setForm(INITIAL_FORM);
                    setShowForm(false);
                  }}
                >
                  Abbrechen
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Lots Table */}
        <div className="panel">
          <div className="panelHeader">
            <h2 className="panelTitle">Alle Lots</h2>
            <span className="badge">{lots.length} Eintraege</span>
          </div>

          {lots.length > 0 ? (
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Kooperative</th>
                    <th>Erntejahr</th>
                    <th>Incoterm</th>
                    <th>Preis/kg</th>
                    <th>Gewicht</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {lots.map((lot) => (
                    <tr key={lot.id}>
                      <td>
                        <Link 
                          href={`/lots/${lot.id}`}
                          style={{ fontWeight: 600, color: "var(--color-text)" }}
                        >
                          {lot.name}
                        </Link>
                      </td>
                      <td>
                        <Link 
                          href={`/cooperatives/${lot.cooperative_id}`}
                          className="badge"
                        >
                          #{lot.cooperative_id}
                        </Link>
                      </td>
                      <td>{lot.crop_year || "-"}</td>
                      <td>
                        {lot.incoterm ? (
                          <span className="badge">{lot.incoterm}</span>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td>
                        {lot.price_per_kg != null ? (
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--font-size-sm)" }}>
                            {lot.price_per_kg.toFixed(2)} {lot.currency || "USD"}
                          </span>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td>
                        {lot.weight_kg != null
                          ? lot.weight_kg >= 1000
                            ? `${(lot.weight_kg / 1000).toFixed(1)}t`
                            : `${lot.weight_kg}kg`
                          : "-"}
                      </td>
                      <td>
                        {lot.expected_cupping_score ? (
                          <span className={`badge ${
                            lot.expected_cupping_score >= 85 ? "badgeOk" :
                            lot.expected_cupping_score >= 80 ? "badgeWarn" : ""
                          }`}>
                            {lot.expected_cupping_score}
                          </span>
                        ) : (
                          <span className="badge">-</span>
                        )}
                      </td>
                      <td>
                        {lot.deleted_at ? (
                          <span className="badge badgeWarn">Archiviert</span>
                        ) : (
                          <span className="badge badgeOk">Aktiv</span>
                        )}
                      </td>
                      <td>
                        <div className="tableActions">
                          <Link href={`/lots/${lot.id}`} className="btn btnSm btnGhost">
                            Details
                          </Link>
                          {lot.deleted_at ? (
                            <button
                              className="btn btnSm"
                              onClick={() => restoreLot(lot.id)}
                              disabled={busyId === lot.id}
                            >
                              Wiederherstellen
                            </button>
                          ) : (
                            <button
                              className="btn btnSm btnDanger"
                              onClick={() => archiveLot(lot.id)}
                              disabled={busyId === lot.id}
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
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                </svg>
                <h3 className="h4">Keine Lots vorhanden</h3>
                <p className="subtitle">
                  Erstellen Sie ein neues Lot, um Kaffeemengen zu verwalten.
                </p>
                <button 
                  type="button" 
                  className="btn btnPrimary"
                  onClick={() => setShowForm(true)}
                  style={{ marginTop: "var(--space-4)" }}
                >
                  Erstes Lot anlegen
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
