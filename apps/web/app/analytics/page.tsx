"use client";

import { useState } from "react";
import { useFreightPrediction, usePricePrediction } from "../hooks/usePredictions";
import { useCooperatives } from "../hooks/usePeruRegions";
import { useRoasters } from "../hooks/useRoasters";
import MarketPriceWidget from "../components/MarketPriceWidget";

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

  const handleFreightPredict = () => {
    freightMutation.mutate(freightForm);
  };

  const handlePricePredict = () => {
    priceMutation.mutate(priceForm);
  };

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Analytik & ML-Vorhersagen</div>
          <div className="muted">
            Verwenden Sie Machine-Learning-Modelle zur Vorhersage von Frachtkosten, Kaffeepreisen und Trends
          </div>
        </div>
      </div>

      {/* Business Intelligence Cards */}
      <div className="grid gridCols4" style={{ marginBottom: "18px" }}>
        <MarketPriceWidget />
        <div className="panel card">
          <div className="cardLabel">Aktive Kooperativen</div>
          <div className="cardValue">{coopsData?.total || 0}</div>
          <div className="cardHint">In Peru Sourcing-Datenbank</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Deutsche Röstereien</div>
          <div className="cardValue">{roastersData?.total || 0}</div>
          <div className="cardHint">In Vertriebspipeline</div>
        </div>
        <div className="panel card">
          <div className="cardLabel">Durchschn. Qualitäts-Score</div>
          <div className="cardValue">
            {coopsData?.items.length
              ? (
                  coopsData.items.reduce((sum, c) => sum + (c.quality_score || 0), 0) /
                  coopsData.items.length
                ).toFixed(1)
              : "–"}
          </div>
          <div className="cardHint">Kooperativen-Qualität</div>
        </div>
      </div>

      <div className="grid gridCols2" style={{ marginBottom: "18px" }}>
        {/* Freight Cost Predictor */}
        <div className="panel" style={{ padding: "18px" }}>
          <div className="h2">Frachtkostenvorhersage</div>
          <div className="muted" style={{ marginBottom: "14px" }}>
            Schätzung der Versandkosten für Kaffeecontainer
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "14px" }}>
            <div>
              <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                Abgangshafen
              </label>
              <input
                type="text"
                className="input"
                value={freightForm.origin_port}
                onChange={(e) => setFreightForm({ ...freightForm, origin_port: e.target.value })}
              />
            </div>
            <div>
              <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                Zielhafen
              </label>
              <input
                type="text"
                className="input"
                value={freightForm.destination_port}
                onChange={(e) =>
                  setFreightForm({ ...freightForm, destination_port: e.target.value })
                }
              />
            </div>
            <div className="grid gridCols2" style={{ gap: "10px" }}>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                  Gewicht (kg)
                </label>
                <input
                  type="number"
                  className="input"
                  value={freightForm.weight_kg}
                  onChange={(e) =>
                    setFreightForm({ ...freightForm, weight_kg: Number(e.target.value) })
                  }
                />
              </div>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                  Containertyp
                </label>
                <select
                  className="input"
                  value={freightForm.container_type}
                  onChange={(e) =>
                    setFreightForm({ ...freightForm, container_type: e.target.value })
                  }
                >
                  <option value="20ft">20ft</option>
                  <option value="40ft">40ft</option>
                </select>
              </div>
            </div>
            <div>
              <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                Abfahrtsdatum
              </label>
              <input
                type="date"
                className="input"
                value={freightForm.departure_date}
                onChange={(e) =>
                  setFreightForm({ ...freightForm, departure_date: e.target.value })
                }
              />
            </div>
          </div>

          <button
            type="button"
            className="btn btnPrimary"
            onClick={handleFreightPredict}
            disabled={freightMutation.isPending}
            style={{ width: "100%" }}
          >
            {freightMutation.isPending ? "Berechne..." : "Frachtkosten vorhersagen"}
          </button>

          {freightMutation.isSuccess && freightMutation.data && (
            <div
              className="panel"
              style={{
                marginTop: "14px",
                padding: "14px",
                background: "rgba(200,149,108,0.08)",
                border: "1px solid rgba(200,149,108,0.25)",
              }}
            >
              <div style={{ fontWeight: "700", marginBottom: "8px" }}>Vorhersageergebnis</div>
              <div style={{ fontSize: "24px", fontWeight: "800", marginBottom: "8px" }}>
                ${freightMutation.data.predicted_cost_usd.toLocaleString()}
              </div>
              <div style={{ fontSize: "13px", color: "var(--muted)" }}>
                Konfidenz: {(freightMutation.data.confidence_score * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: "13px", color: "var(--muted)", marginTop: "4px" }}>
                Bereich: ${freightMutation.data.confidence_interval_low.toLocaleString()} - $
                {freightMutation.data.confidence_interval_high.toLocaleString()}
              </div>
              {freightMutation.data.similar_historical_shipments > 0 && (
                <div style={{ fontSize: "13px", color: "var(--muted)", marginTop: "4px" }}>
                  Basierend auf {freightMutation.data.similar_historical_shipments} ähnlichen Sendungen
                </div>
              )}
            </div>
          )}

          {freightMutation.isError && (
            <div className="alert bad" style={{ marginTop: "14px" }}>
              <div className="alertTitle">Vorhersage fehlgeschlagen</div>
              <div className="alertText">
                {freightMutation.error instanceof Error 
                  ? freightMutation.error.message 
                  : "Frachtkosten konnten nicht vorhergesagt werden"}
              </div>
            </div>
          )}
        </div>

        {/* Coffee Price Predictor */}
        <div className="panel" style={{ padding: "18px" }}>
          <div className="h2">Kaffeepreisvorhersage</div>
          <div className="muted" style={{ marginBottom: "14px" }}>
            Kaffeepreise basierend auf Qualität und Eigenschaften vorhersagen
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "14px" }}>
            <div className="grid gridCols2" style={{ gap: "10px" }}>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                  Herkunftsland
                </label>
                <input
                  type="text"
                  className="input"
                  value={priceForm.origin_country}
                  onChange={(e) => setPriceForm({ ...priceForm, origin_country: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                  Region
                </label>
                <input
                  type="text"
                  className="input"
                  value={priceForm.origin_region}
                  onChange={(e) => setPriceForm({ ...priceForm, origin_region: e.target.value })}
                />
              </div>
            </div>
            <div className="grid gridCols2" style={{ gap: "10px" }}>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                  Sorte
                </label>
                <input
                  type="text"
                  className="input"
                  value={priceForm.variety}
                  onChange={(e) => setPriceForm({ ...priceForm, variety: e.target.value })}
                />
              </div>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                  Prozess
                </label>
                <select
                  className="input"
                  value={priceForm.process}
                  onChange={(e) => setPriceForm({ ...priceForm, process: e.target.value })}
                >
                  <option value="Washed">Gewaschen</option>
                  <option value="Natural">Natürlich</option>
                  <option value="Honey">Honey</option>
                </select>
              </div>
            </div>
            <div>
              <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                Qualität
              </label>
              <input
                type="text"
                className="input"
                value={priceForm.grade}
                onChange={(e) => setPriceForm({ ...priceForm, grade: e.target.value })}
              />
            </div>
            <div>
              <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                Cupping Score
              </label>
              <input
                type="number"
                className="input"
                min="0"
                max="100"
                value={priceForm.cupping_score}
                onChange={(e) =>
                  setPriceForm({ ...priceForm, cupping_score: Number(e.target.value) })
                }
              />
            </div>
            <div>
              <label style={{ fontSize: "12px", color: "var(--muted)", display: "block", marginBottom: "6px" }}>
                Prognosedatum
              </label>
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
            className="btn btnPrimary"
            onClick={handlePricePredict}
            disabled={priceMutation.isPending}
            style={{ width: "100%" }}
          >
            {priceMutation.isPending ? "Berechne..." : "Preis vorhersagen"}
          </button>

          {priceMutation.isSuccess && priceMutation.data && (
            <div
              className="panel"
              style={{
                marginTop: "14px",
                padding: "14px",
                background: "rgba(64,214,123,0.08)",
                border: "1px solid rgba(64,214,123,0.25)",
              }}
            >
              <div style={{ fontWeight: "700", marginBottom: "8px" }}>Vorhersageergebnis</div>
              <div style={{ fontSize: "24px", fontWeight: "800", marginBottom: "8px" }}>
                ${priceMutation.data.predicted_price_usd_per_kg.toFixed(2)}/kg
              </div>
              <div style={{ fontSize: "13px", color: "var(--muted)" }}>
                Konfidenz: {(priceMutation.data.confidence_score * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: "13px", color: "var(--muted)", marginTop: "4px" }}>
                Bereich: ${priceMutation.data.confidence_interval_low.toFixed(2)} - $
                {priceMutation.data.confidence_interval_high.toFixed(2)}/kg
              </div>
              {priceMutation.data.price_trend && (
                <div style={{ fontSize: "13px", color: "var(--muted)", marginTop: "4px" }}>
                  Trend: {priceMutation.data.price_trend}
                </div>
              )}
              {priceMutation.data.market_comparison && (
                <div style={{ fontSize: "13px", color: "var(--muted)", marginTop: "4px" }}>
                  {priceMutation.data.market_comparison}
                </div>
              )}
            </div>
          )}

          {priceMutation.isError && (
            <div className="alert bad" style={{ marginTop: "14px" }}>
              <div className="alertTitle">Vorhersage fehlgeschlagen</div>
              <div className="alertText">
                {priceMutation.error instanceof Error 
                  ? priceMutation.error.message 
                  : "Preis konnte nicht vorhergesagt werden"}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Info Panel */}
      <div className="panel" style={{ padding: "18px" }}>
        <div className="h2">Über ML-Vorhersagen</div>
        <div className="muted" style={{ marginTop: "10px" }}>
          Diese Vorhersagen werden durch Machine-Learning-Modelle unterstützt, die auf historischen Daten trainiert wurden. 
          Der Frachtkostenvorhersager verwendet historische Versanddaten zur Schätzung der Containerkosten, während 
          der Kaffeepreisvorhersager Qualitätsmerkmale und Markttrends analysiert. Alle 
          Vorhersagen enthalten Konfidenz-Scores, um Ihnen bei der Beurteilung der Zuverlässigkeit zu helfen.
        </div>
      </div>
    </div>
  );
}
