"use client";

import { useEffect, useState } from "react";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { ErrorPanel } from "../components/AlertError";
import { useToast } from "../components/ToastProvider";
import { toErrorMessage } from "../utils/error";

type MLModel = {
  id: number;
  model_name: string;
  model_type: string;
  algorithm: string | null;
  model_version: string;
  training_date: string;
  performance_metrics: Record<string, unknown> | null;
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
  forecast_days: number;
  current_price: number;
  forecast: Array<{
    date: string;
    predicted_price: number;
    confidence: number;
  }>;
  trend: string;
  note: string;
  message: string;
};

export default function MLPage() {
  const toast = useToast();
  const [models, setModels] = useState<MLModel[]>([]);
  const [purchaseTiming, setPurchaseTiming] = useState<PurchaseTiming | null>(null);
  const [forecast, setForecast] = useState<PriceForecast | null>(null);
  const [trainingModel, setTrainingModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  async function fetchAll() {
    if (isDemoMode()) { setLoading(false); return; }
    setLoading(true);
    setErr(null);
    try {
      const [modelsData, timingData, forecastData] = await Promise.allSettled([
        apiFetch<MLModel[]>("/ml/train/training-status"),
        apiFetch<PurchaseTiming>("/ml/train/optimal-purchase-timing"),
        apiFetch<PriceForecast>("/ml/train/price-forecast?days=30"),
      ]);
      if (modelsData.status === "fulfilled") setModels(Array.isArray(modelsData.value) ? modelsData.value : []);
      if (timingData.status === "fulfilled") setPurchaseTiming(timingData.value as PurchaseTiming);
      if (forecastData.status === "fulfilled") setForecast(forecastData.value as PriceForecast);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function trainModel(modelType: string) {
    try {
      setTrainingModel(modelType);
      await apiFetch(`/ml/train/${modelType}`, { method: "POST" });
      toast.success(`Modelltraining für ${modelType} gestartet!`);
      fetchAll();
    } catch (error: unknown) {
      toast.error(`Fehler beim Training: ${toErrorMessage(error)}`);
    } finally {
      setTrainingModel(null);
    }
  }

  useEffect(() => {
    fetchAll();
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
    <div className="content">
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <div className="h1">ML-Modelle</div>
          <div className="muted">Machine Learning Modelle und Kaufzeitprognosen</div>
        </div>
        <div className="pageHeaderActions">
          <button
            className="btn btnPrimary"
            onClick={() => trainModel("freight_cost")}
            disabled={!!trainingModel || loading}
          >
            {trainingModel === "freight_cost" ? "Training läuft..." : "Frachtmodell trainieren"}
          </button>
          <button
            className="btn btnPrimary"
            onClick={() => trainModel("coffee_price")}
            disabled={!!trainingModel || loading}
          >
            {trainingModel === "coffee_price" ? "Training läuft..." : "Preismodell trainieren"}
          </button>
        </div>
      </header>

      {err && <ErrorPanel message={err} onRetry={fetchAll} />}

      <div className="grid2col" style={{ marginBottom: "var(--space-5)" }}>
        {/* Kaufzeitempfehlung */}
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Kaufzeitempfehlung</div>
          </div>
          <div className="panelBody">
            {loading ? (
              <div className="muted">Lädt...</div>
            ) : !purchaseTiming ? (
              <EmptyState icon={
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
              } title="Keine Empfehlung" text="Backend nicht erreichbar oder keine Marktdaten vorhanden." />
            ) : (
              <div>
                <div style={{ marginBottom: "var(--space-3)" }}>
                  {recommendationBadge(purchaseTiming.recommendation)}
                </div>
                <div style={{ marginBottom: "var(--space-2)" }}>
                  <strong>Vertrauen:</strong> {(purchaseTiming.confidence * 100).toFixed(0)}%
                </div>
                <div className="muted" style={{ marginBottom: "var(--space-4)" }}>
                  {purchaseTiming.reason}
                </div>
                <div className="grid2col">
                  <div>
                    <div className="fieldLabel">Aktueller Preis</div>
                    <div>${purchaseTiming.current_price.toFixed(2)}/kg</div>
                  </div>
                  <div>
                    <div className="fieldLabel">Durchschnittspreis</div>
                    <div>${purchaseTiming.average_price.toFixed(2)}/kg</div>
                  </div>
                </div>
                <div style={{ marginTop: "var(--space-3)" }}>
                  <div className="fieldLabel">Trend</div>
                  <Badge tone="neutral">{purchaseTiming.trend}</Badge>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Preisprognose */}
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Preisprognose (30 Tage)</div>
          </div>
          <div className="panelBody">
            {loading ? (
              <div className="muted">Lädt...</div>
            ) : !forecast || forecast.status !== "ok" || !forecast.forecast ? (
              <EmptyState icon={
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              } title="Keine Prognose" text={forecast?.message ?? "Backend nicht erreichbar."} />
            ) : (
              <div>
                <div className="muted" style={{ marginBottom: "var(--space-3)" }}>
                  {forecast.note}
                </div>
              <div className="tableWrap">
                <table className="table">
                    <thead>
                      <tr>
                        <th>Datum</th>
                        <th>Preis</th>
                        <th>Konfidenz</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecast.forecast.slice(0, 10).map((f, idx) => (
                        <tr key={idx}>
                          <td>{new Date(f.date).toLocaleDateString("de-DE")}</td>
                          <td>${f.predicted_price.toFixed(2)}/kg</td>
                          <td><Badge tone="neutral">{(f.confidence * 100).toFixed(0)}%</Badge></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modellstatus */}
      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Modellstatus</div>
          <span className="badge">{models.length} Modelle</span>
        </div>
        {loading ? (
          <SkeletonRows rows={4} cols={6} />
        ) : models.length === 0 ? (
          <EmptyState icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
          } title="Keine Modelle" text="Es wurden noch keine ML-Modelle trainiert." />
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
                    <td>{new Date(model.training_date).toLocaleDateString("de-DE")}</td>
                    <td>
                      {model.performance_metrics ? (
                        <div style={{ fontSize: "var(--font-size-xs)" }}>
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
