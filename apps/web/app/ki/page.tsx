"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ErrorPanel } from "../components/AlertError";
import Badge from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { ApiError, apiFetch, isDemoMode } from "../../lib/api";

interface AssistantStatus {
  available: boolean;
  enabled: boolean;
  provider: string;
  model: string;
}

interface AnalystStatus {
  available: boolean;
  provider: string;
  model: string;
  embedding_provider: string;
  embedding_model: string;
}

const WORKSPACES = [
  {
    href: "/assistant",
    title: "Assistant Chat",
    description: "Interaktiver Streaming-Chat fuer operative Fragen und schnelle Recherche.",
    badge: "Chat",
  },
  {
    href: "/analyst",
    title: "KI-Analyst",
    description: "Analytische Antworten mit Quellenbezug fuer Sourcing, Markt und Bestand.",
    badge: "RAG",
  },
  {
    href: "/search",
    title: "Semantische Suche",
    description: "Direkter Einstieg in Kooperativen- und Roestereisuchen ueber Embeddings.",
    badge: "Search",
  },
];

const QUICK_LINKS = [
  { href: "/pipeline", label: "Data Pipeline pruefen" },
  { href: "/features", label: "ML Features kontrollieren" },
  { href: "/markt", label: "Marktansicht oeffnen" },
];

function statusTone(available: boolean, enabled = true) {
  if (!enabled) return "warn";
  return available ? "good" : "bad";
}

function providerLabel(provider: string) {
  if (provider === "ollama") return "Ollama";
  if (provider === "openai") return "OpenAI";
  if (provider === "groq") return "Groq";
  return provider || "Unbekannt";
}

export default function KIPage() {
  const [assistantStatus, setAssistantStatus] = useState<AssistantStatus | null>(null);
  const [analystStatus, setAnalystStatus] = useState<AnalystStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      if (isDemoMode()) {
        if (!active) return;
        setLoading(false);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const [assistant, analyst] = await Promise.all([
          apiFetch<AssistantStatus>("/assistant/status"),
          apiFetch<AnalystStatus>("/analyst/status"),
        ]);
        if (!active) return;
        setAssistantStatus(assistant);
        setAnalystStatus(analyst);
      } catch (err) {
        if (!active) return;
        if (err instanceof ApiError && err.status === 401) {
          setError("Authentifizierung erforderlich. Bitte erneut anmelden.");
        } else {
          setError(err instanceof Error ? err.message : "KI-Status konnte nicht geladen werden.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  const assistantReady = !!assistantStatus?.available && assistantStatus.enabled;
  const analystReady = !!analystStatus?.available;
  const overallReady = assistantReady || analystReady;

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <h1 className="h1">KI-Arbeitsbereich</h1>
          <p className="muted">
            Zentrale Leitstelle fuer Assistant, Analyst und semantische Suche.
          </p>
        </div>
        <div className="pageActions">
          <Badge tone={isDemoMode() ? "warn" : overallReady ? "good" : "warn"}>
            {isDemoMode() ? "Demo-Modus" : overallReady ? "Teilweise bereit" : "Pruefung noetig"}
          </Badge>
        </div>
      </div>

      {error && <ErrorPanel compact message={error} />}

      <div className="kpiGrid" style={{ marginBottom: "var(--space-5)" }}>
        <div className="kpiCard">
          <div className="kpiLabel">Assistant</div>
          <div className="kpiValue">
            {loading ? "..." : assistantStatus?.enabled ? (assistantStatus.available ? "Bereit" : "Offline") : "Deaktiviert"}
          </div>
          <div className="kpiMeta">
            {assistantStatus ? `${providerLabel(assistantStatus.provider)} · ${assistantStatus.model}` : "Streaming-Chat"}
          </div>
        </div>

        <div className="kpiCard">
          <div className="kpiLabel">Analyst</div>
          <div className="kpiValue">{loading ? "..." : analystStatus?.available ? "Bereit" : "Offline"}</div>
          <div className="kpiMeta">
            {analystStatus
              ? `${providerLabel(analystStatus.provider)} · ${analystStatus.model}`
              : "RAG-Analyse"}
          </div>
        </div>

        <div className="kpiCard">
          <div className="kpiLabel">Embeddings</div>
          <div className="kpiValue">{loading ? "..." : analystStatus?.embedding_provider || "n/a"}</div>
          <div className="kpiMeta">{analystStatus?.embedding_model || "Suche und Kontext"}</div>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: "var(--space-5)" }}>
        <div className="panelHeader">
          <div className="panelTitle">Arbeitsbereiche</div>
        </div>
        <div className="panelBody">
          <div className="cardGrid">
            {WORKSPACES.map((workspace) => {
              const tone =
                workspace.href === "/assistant"
                  ? statusTone(!!assistantStatus?.available, assistantStatus?.enabled ?? false)
                  : workspace.href === "/analyst"
                    ? statusTone(!!analystStatus?.available)
                    : "info";

              return (
                <div key={workspace.href} className="panel" style={{ marginBottom: 0 }}>
                  <div className="panelBody">
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-3)" }}>
                      <div style={{ fontWeight: "var(--font-weight-semibold)", color: "var(--color-text)" }}>
                        {workspace.title}
                      </div>
                      <Badge tone={tone as "neutral" | "good" | "warn" | "bad" | "info"}>
                        {workspace.badge}
                      </Badge>
                    </div>
                    <p className="muted" style={{ marginBottom: "var(--space-4)" }}>
                      {workspace.description}
                    </p>
                    <Link className="btn btnPrimary" href={workspace.href}>
                      Oeffnen
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: "var(--space-5)" }}>
        <div className="panelHeader">
          <div className="panelTitle">Systemstatus</div>
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Modul</th>
                <th>Status</th>
                <th>Provider</th>
                <th>Modell</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Assistant</td>
                <td>
                  <Badge tone={statusTone(!!assistantStatus?.available, assistantStatus?.enabled ?? false)}>
                    {loading ? "Laden" : assistantStatus?.enabled ? (assistantStatus.available ? "Bereit" : "Offline") : "Deaktiviert"}
                  </Badge>
                </td>
                <td className="muted">{assistantStatus ? providerLabel(assistantStatus.provider) : "—"}</td>
                <td className="muted">{assistantStatus?.model || "—"}</td>
              </tr>
              <tr>
                <td>Analyst</td>
                <td>
                  <Badge tone={statusTone(!!analystStatus?.available)}>
                    {loading ? "Laden" : analystStatus?.available ? "Bereit" : "Offline"}
                  </Badge>
                </td>
                <td className="muted">{analystStatus ? providerLabel(analystStatus.provider) : "—"}</td>
                <td className="muted">{analystStatus?.model || "—"}</td>
              </tr>
              <tr>
                <td>Embeddings</td>
                <td>
                  <Badge tone={analystStatus?.embedding_provider ? "info" : "warn"}>
                    {loading ? "Laden" : analystStatus?.embedding_provider || "Nicht erkannt"}
                  </Badge>
                </td>
                <td className="muted">{analystStatus?.embedding_provider || "—"}</td>
                <td className="muted">{analystStatus?.embedding_model || "—"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Naechste sinnvolle Schritte</div>
        </div>
        <div className="panelBody">
          {isDemoMode() ? (
            <EmptyState
              title="KI-Funktionen im Demo-Modus eingeschraenkt"
              description="Melden Sie sich mit einer echten Session an, um Assistant, Analyst und Suche gegen die laufenden APIs zu verwenden."
            />
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-3)" }}>
              {QUICK_LINKS.map((link) => (
                <Link key={link.href} href={link.href} className="btn">
                  {link.label}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
