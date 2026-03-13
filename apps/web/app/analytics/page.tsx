"use client";

import { useState } from "react";
import { useFreightPrediction, usePricePrediction } from "../hooks/usePredictions";
import { useCooperatives } from "../hooks/usePeruRegions";
import { useRoasters } from "../hooks/useRoasters";
import MarketPriceWidget from "../components/MarketPriceWidget";
import { ErrorPanel } from "../components/ErrorPanel";

/* ============================================================
   ANALYTICS & ML PREDICTIONS - ENTERPRISE VIEW
   ============================================================ */

export default function AnalyticsDashboard() {
  const [freightForm, setFreightForm] = useState({
    origin_port: "Callao",
    destination_port: "Hamburg",
    weight_kg: 18000,
    container_type: "20ft",
    departure_date: new Date().toISOString().split("T")[0],
  });

  const [priceForm, setPriceForm] = useState({
    origin_country: "Peru",
    origin_region: "Cajamarca",
    variety: "Arabica",
    process: "Washed",
    grade: "SHG",
    cupping_score: 85,
    certifications: ["Organic"],
    forecast_date: new Date().toISOString().split("T")[0],
  });

  const freightMutation = useFreightPrediction();
  const priceMutation = usePricePrediction();

  const { data: coopsData } = useCooperatives({ limit: 5 });
  const { data: roastersData } = useRoasters({ country: "Germany", limit: 5 });
  const coopsTotal = coopsData?.total ?? 0;
  const coopsItems = coopsData?.items ?? [];
  const roastersTotal = roastersData?.total ?? 0;

  const handleFreightPredict = () => {
    freightMutation.mutate(freightForm);
  };

  const handlePricePredict = () => {
    priceMutation.mutate(priceForm);
  };

  return (
    <div className="page">
      <div className="content">
        {/* Page Header */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Analytik & ML-Vorhersagen</h1>
            <p className="subtitle">
              Machine-Learning-Modelle zur Vorhersage von Frachtkosten, Kaffeepreisen und Trends
            </p>
          </div>
        </header>

        {/* KPI Grid with Market Widget */}
        <div className="kpiGrid">
          <MarketPriceWidget />
          <div className="kpiCard">
            <span className="cardLabel">Aktive Kooperativen</span>
            <span className="cardValue">{coopsTotal}</span>
            <span className="cardHint">In Sourcing-Datenbank</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Deutsche Röstereien</span>
            <span className="cardValue">{roastersTotal}</span>
            <span className="cardHint">In Vertriebspipeline</span>
          </div>
          <div className="kpiCard">
            <span className="cardLabel">Durchschn. Qualitaet</span>
            <span className="cardValue">
              {coopsItems.length
                ? (
                    coopsItems.reduce((sum, c) => sum + (c.quality_score || 0), 0) /
                    coopsItems.length
                  ).toFixed(1)
                : "-"}
            </span>
            <span className="cardHint">Kooperativen-Score</span>
          </div>
        </div>

        {/* Prediction Panels */}
        <div className="grid2col">
          {/* Freight Cost Predictor */}
          <div className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Frachtkostenvorhersage</h2>
              <span className="badge badgeInfo">ML-Modell</span>
            </div>
            <div className="panelBody">
              <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
                Schätzung der Versandkosten für Kaffeecontainer
              </p>

              <div className="fieldStack">
                <div className="fieldGrid2">
                  <div className="field">
                    <label className="fieldLabel">Abgangshafen</label>
                    <input
                      type="text"
                      className="input"
                      value={freightForm.origin_port}
                      onChange={(e) => setFreightForm({ ...freightForm, origin_port: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Zielhafen</label>
                    <input
                      type="text"
                      className="input"
                      value={freightForm.destination_port}
                      onChange={(e) => setFreightForm({ ...freightForm, destination_port: e.target.value })}
                    />
                  </div>
                </div>
                <div className="fieldGrid2">
                  <div className="field">
                    <label className="fieldLabel">Gewicht (kg)</label>
                    <input
                      type="number"
                      className="input"
                      value={freightForm.weight_kg}
                      onChange={(e) => setFreightForm({ ...freightForm, weight_kg: Number(e.target.value) })}
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Containertyp</label>
                    <select
                      className="input"
                      value={freightForm.container_type}
                      onChange={(e) => setFreightForm({ ...freightForm, container_type: e.target.value })}
                    >
                      <option value="20ft">20ft</option>
                      <option value="40ft">40ft</option>
                    </select>
                  </div>
                </div>
                <div className="field">
                  <label className="fieldLabel">Abfahrtsdatum</label>
                  <input
                    type="date"
                    className="input"
                    value={freightForm.departure_date}
                    onChange={(e) => setFreightForm({ ...freightForm, departure_date: e.target.value })}
                  />
                </div>
              </div>

              <button
                type="button"
                className="btn btnPrimary btnFull"
                onClick={handleFreightPredict}
                disabled={freightMutation.isPending}
              >
                {freightMutation.isPending ? "Berechne..." : "Frachtkosten vorhersagen"}
              </button>

              {freightMutation.isSuccess && freightMutation.data && (
                <div className="predictionResult">
                  <h4 className="h4">Vorhersageergebnis</h4>
                  <div className="predictionValue">
                    ${freightMutation.data.predicted_cost_usd.toLocaleString()}
                  </div>
                  <div className="predictionMeta">
                    <span>Konfidenz: {(freightMutation.data.confidence_score * 100).toFixed(1)}%</span>
                    <span>
                      Bereich: ${freightMutation.data.confidence_interval_low.toLocaleString()} - 
                      ${freightMutation.data.confidence_interval_high.toLocaleString()}
                    </span>
                    {freightMutation.data.similar_historical_shipments > 0 && (
                      <span>Basierend auf {freightMutation.data.similar_historical_shipments} ähnlichen Sendungen</span>
                    )}
                  </div>
                </div>
              )}

              {freightMutation.isError && (
                <ErrorPanel
                  compact
                  message={freightMutation.error instanceof Error ? freightMutation.error.message : "Unbekannter Fehler"}
                  style={{ marginTop: "var(--space-4)" }}
                />
              )}
            </div>
          </div>

          {/* Coffee Price Predictor */}
          <div className="panel">
            <div className="panelHeader">
              <h2 className="panelTitle">Kaffeepreisvorhersage</h2>
              <span className="badge badgeInfo">ML-Modell</span>
            </div>
            <div className="panelBody">
              <p className="subtitle" style={{ marginBottom: "var(--space-4)" }}>
                Kaffeepreise basierend auf Qualitaet und Eigenschaften vorhersagen
              </p>

              <div className="fieldStack">
                <div className="fieldGrid2">
                  <div className="field">
                    <label className="fieldLabel">Herkunftsland</label>
                    <input
                      type="text"
                      className="input"
                      value={priceForm.origin_country}
                      onChange={(e) => setPriceForm({ ...priceForm, origin_country: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Region</label>
                    <input
                      type="text"
                      className="input"
                      value={priceForm.origin_region}
                      onChange={(e) => setPriceForm({ ...priceForm, origin_region: e.target.value })}
                    />
                  </div>
                </div>
                <div className="fieldGrid2">
                  <div className="field">
                    <label className="fieldLabel">Sorte</label>
                    <input
                      type="text"
                      className="input"
                      value={priceForm.variety}
                      onChange={(e) => setPriceForm({ ...priceForm, variety: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Prozess</label>
                    <select
                      className="input"
                      value={priceForm.process}
                      onChange={(e) => setPriceForm({ ...priceForm, process: e.target.value })}
                    >
                      <option value="Washed">Gewaschen</option>
                      <option value="Natural">Natuerlich</option>
                      <option value="Honey">Honey</option>
                    </select>
                  </div>
                </div>
                <div className="fieldGrid2">
                  <div className="field">
                    <label className="fieldLabel">Qualitaet</label>
                    <input
                      type="text"
                      className="input"
                      value={priceForm.grade}
                      onChange={(e) => setPriceForm({ ...priceForm, grade: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label className="fieldLabel">Cupping Score</label>
                    <input
                      type="number"
                      className="input"
                      min="0"
                      max="100"
                      value={priceForm.cupping_score}
                      onChange={(e) => setPriceForm({ ...priceForm, cupping_score: Number(e.target.value) })}
                    />
                  </div>
                </div>
                <div className="field">
                  <label className="fieldLabel">Prognosedatum</label>
                  <input
                    type="date"
                    className="input"
                    value={priceForm.forecast_date}
                    onChange={(e) => setPriceForm({ ...priceForm, forecast_date: e.target.value })}
                  />
                </div>
              </div>

              <button
                type="button"
                className="btn btnPrimary btnFull"
                onClick={handlePricePredict}
                disabled={priceMutation.isPending}
              >
                {priceMutation.isPending ? "Berechne..." : "Preis vorhersagen"}
              </button>

              {priceMutation.isSuccess && priceMutation.data && (
                <div className="predictionResult success">
                  <h4 className="h4">Vorhersageergebnis</h4>
                  <div className="predictionValue">
                    ${priceMutation.data.predicted_price_usd_per_kg.toFixed(2)}/kg
                  </div>
                  <div className="predictionMeta">
                    <span>Konfidenz: {(priceMutation.data.confidence_score * 100).toFixed(1)}%</span>
                    <span>
                      Bereich: ${priceMutation.data.confidence_interval_low.toFixed(2)} - 
                      ${priceMutation.data.confidence_interval_high.toFixed(2)}/kg
                    </span>
                    {priceMutation.data.price_trend && (
                      <span>Trend: {priceMutation.data.price_trend}</span>
                    )}
                  </div>
                </div>
              )}

              {priceMutation.isError && (
                <ErrorPanel
                  compact
                  message={priceMutation.error instanceof Error ? priceMutation.error.message : "Unbekannter Fehler"}
                  style={{ marginTop: "var(--space-4)" }}
                />
              )}
            </div>
          </div>
        </div>

        {/* Info Panel */}
        <div className="panel" style={{ marginTop: "var(--space-6)" }}>
          <div className="panelHeader">
            <h2 className="panelTitle">Ueber ML-Vorhersagen</h2>
          </div>
          <div className="panelBody">
            <p className="subtitle">
              Diese Vorhersagen werden durch Machine-Learning-Modelle unterstuetzt, die auf historischen Daten trainiert wurden. 
              Der Frachtkostenvorhersager verwendet historische Versanddaten zur Schaetzung der Containerkosten, waehrend 
              der Kaffeepreisvorhersager Qualitaetsmerkmale und Markttrends analysiert. Alle 
              Vorhersagen enthalten Konfidenz-Scores zur Beurteilung der Zuverlaessigkeit.
            </p>
          </div>
        </div>
      </div>

      <style jsx>{`
        .predictionResult {
          margin-top: var(--space-4);
          padding: var(--space-4);
          background: var(--color-accent-subtle);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
        }
        .predictionResult.success {
          background: var(--color-success-subtle);
          border-color: var(--color-success-border);
        }
        .predictionValue {
          font-size: var(--font-size-3xl);
          font-weight: var(--font-weight-bold);
          color: var(--color-text);
          margin: var(--space-2) 0;
          font-family: var(--font-mono);
        }
        .predictionMeta {
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
          font-size: var(--font-size-sm);
          color: var(--color-text-muted);
        }
      `}</style>
    </div>
  );
}
