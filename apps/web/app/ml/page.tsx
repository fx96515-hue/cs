"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

type MLModel = {
  id: number;
  model_name: string;
  model_type: string;
  algorithm: string | null;
  model_version: string;
  training_date: string;
  performance_metrics: any;
  training_data_count: number;
  status: string;
};

type PurchaseTiming = {
  recommendation: string;
  confidence: number;
  reason: string;
  current_price: number;
  average_price: number;
  trend: string;
  volatility: number;
  current_month: number;
};

type PriceForecast = {
  status: string;
  forecast_days?: number;
  current_price?: number;
  forecast?: Array<{
    date: string;
    predicted_price: number;
    confidence: number;
  }>;
  trend?: string;
  note?: string;
  message?: string;
};

export default function MLPage() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [purchaseTiming, setPurchaseTiming] = useState<PurchaseTiming | null>(
    null
  );
  const [forecast, setForecast] = useState<PriceForecast | null>(null);
  const [trainingModel, setTrainingModel] = useState<string | null>(null);

  async function fetchModels() {
    try {
      const data = await apiFetch<MLModel[]>("/ml/train/training-status");
      setModels(data);
    } catch (e) {
      console.error("Failed to fetch models:", e);
    }
  }

  async function fetchPurchaseTiming() {
    try {
      const data = await apiFetch<PurchaseTiming>(
        "/ml/train/optimal-purchase-timing"
      );
      setPurchaseTiming(data);
    } catch (e) {
      console.error("Failed to fetch purchase timing:", e);
    }
  }

  async function fetchForecast() {
    try {
      const data = await apiFetch<PriceForecast>(
        "/ml/train/price-forecast?days=30"
      );
      setForecast(data);
    } catch (e) {
      console.error("Failed to fetch forecast:", e);
    }
  }

  async function trainModel(modelType: string) {
    try {
      setTrainingModel(modelType);
      await apiFetch(`/ml/train/${modelType}`, { method: "POST" });
      alert(`Modelltraining für ${modelType} gestartet!`);
      fetchModels();
    } catch (e: any) {
      alert(`Fehler beim Training: ${e?.message || e}`);
    } finally {
      setTrainingModel(null);
    }
  }

  useEffect(() => {
    fetchModels();
    fetchPurchaseTiming();
    fetchForecast();
  }, []);

  const recommendationBadge = (rec: string) => {
    if (rec === "buy_now") return <Badge tone="good">Jetzt kaufen</Badge>;
    if (rec === "wait") return <Badge tone="warn">Warten</Badge>;
    return <Badge tone="neutral">Genau beobachten</Badge>;
  };

  const statusBadge = (status: string) => {
    const tone = status === "active" ? "good" : "neutral";
    return <Badge tone={tone}>{status}</Badge>;
  };

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">ML-Modelle</div>
          <div className="muted">
            Machine Learning Modelle und Kaufzeitprognosen
          </div>
        </div>
      </div>

      <div className="grid2" style={{ marginBottom: 20 }}>
        <div className="panel">
          <div className="panelTitle">Kaufzeitempfehlung</div>
          {purchaseTiming ? (
            <div>
              <div style={{ marginBottom: 10 }}>
                {recommendationBadge(purchaseTiming.recommendation)}
                <div style={{ marginTop: 8 }}>
                  <strong>Vertrauen:</strong>{" "}
                  {(purchaseTiming.confidence * 100).toFixed(0)}%
                </div>
              </div>
              <div className="muted">{purchaseTiming.reason}</div>
              <div style={{ marginTop: 14 }}>
                <div className="row gap">
                  <div>
                    <div className="label">Aktueller Preis</div>
                    <div>${purchaseTiming.current_price.toFixed(2)}/kg</div>
                  </div>
                  <div>
                    <div className="label">Durchschnittspreis</div>
                    <div>${purchaseTiming.average_price.toFixed(2)}/kg</div>
                  </div>
                </div>
                <div style={{ marginTop: 8 }}>
                  <div className="label">Trend</div>
                  <Badge tone="neutral">{purchaseTiming.trend}</Badge>
                </div>
              </div>
            </div>
          ) : (
            <div className="muted">Lädt...</div>
          )}
        </div>

        <div className="panel">
          <div className="panelTitle">Preisprognose (30 Tage)</div>
          {forecast && forecast.status === "ok" && forecast.forecast ? (
            <div>
              <div className="muted" style={{ marginBottom: 10 }}>
                {forecast.note}
              </div>
              <div style={{ maxHeight: 200, overflowY: "auto" }}>
                {forecast.forecast.slice(0, 10).map((f, idx) => (
                  <div key={idx} className="row" style={{ padding: 4 }}>
                    <div style={{ flex: 1 }}>
                      {new Date(f.date).toLocaleDateString("de-DE")}
                    </div>
                    <div style={{ flex: 1 }}>
                      ${f.predicted_price.toFixed(2)}/kg
                    </div>
                    <div style={{ flex: 1 }}>
                      <Badge tone="neutral">
                        {(f.confidence * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="muted">
              {forecast?.message || "Lädt..."}
            </div>
          )}
        </div>
      </div>

      <div className="panel">
        <div className="panelTitle">Modellstatus</div>
        <div className="row gap" style={{ marginBottom: 14 }}>
          <button
            className="btn btnPrimary"
            onClick={() => trainModel("freight_cost")}
            disabled={trainingModel === "freight_cost"}
          >
            {trainingModel === "freight_cost"
              ? "Training läuft..."
              : "Frachtmodell trainieren"}
          </button>
          <button
            className="btn btnPrimary"
            onClick={() => trainModel("coffee_price")}
            disabled={trainingModel === "coffee_price"}
          >
            {trainingModel === "coffee_price"
              ? "Training läuft..."
              : "Preismodell trainieren"}
          </button>
        </div>

        {models.length === 0 ? (
          <div className="muted">Keine Modelle vorhanden.</div>
        ) : (
          <div className="table">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Typ</th>
                  <th>Algorithmus</th>
                  <th>Version</th>
                  <th>Trainingsdatum</th>
                  <th>Metriken</th>
                  <th>Stichproben</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.id}>
                    <td>{model.model_name}</td>
                    <td>{model.model_type}</td>
                    <td>
                      <Badge tone={model.algorithm === "xgboost" ? "good" : "neutral"}>
                        {model.algorithm ?? "random_forest"}
                      </Badge>
                    </td>
                    <td>{model.model_version}</td>
                    <td>
                      {new Date(model.training_date).toLocaleDateString("de-DE")}
                    </td>
                    <td>
                      {model.performance_metrics ? (
                        <div style={{ fontSize: "0.85em" }}>
                          {Object.entries(model.performance_metrics)
                            .slice(0, 2)
                            .map(([k, v]) => (
                              <div key={k}>
                                {k}: {typeof v === "number" ? v.toFixed(3) : String(v)}
                              </div>
                            ))}
                        </div>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>{model.training_data_count || "-"}</td>
                    <td>{statusBadge(model.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
