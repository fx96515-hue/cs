"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, getToken, isDemoMode } from "../../lib/api";
import { EmptyState } from "../components/EmptyState";
import { ErrorPanel } from "../components/AlertError";

const MAX_LEN = 1000;

interface Source {
  entity_type: string;
  entity_id: number;
  name: string;
  similarity_score: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources: Source[];
}

interface ServiceStatus {
  available: boolean;
  provider: string;
  model: string;
}

const EXAMPLES = [
  "Welche Kooperativen in Cajamarca haben Fair-Trade-Zertifizierung?",
  "Vergleiche Röstereien in München nach Bewertung.",
  "Beste Regionen für Specialty Coffee in Peru?",
  "Bio-zertifizierte Kooperativen mit Score über 80?",
];

const PROVIDER_LABELS: Record<string, string> = {
  ollama: "Ollama (lokal)",
  openai: "OpenAI",
  groq: "Groq",
};

function TypingIndicator() {
  return (
    <div className="chatTyping">
      <div className="chatTypingDot" />
      <div className="chatTypingDot" />
      <div className="chatTypingDot" />
    </div>
  );
}

function SourceChip({ source }: { source: Source }) {
  const href =
    source.entity_type === "cooperative"
      ? `/cooperatives/${source.entity_id}`
      : source.entity_type === "roaster"
      ? `/roasters/${source.entity_id}`
      : "#";

  return (
    <Link href={href} className="chatSourceChip">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        <polyline points="15 3 21 3 21 9"/>
        <line x1="10" y1="14" x2="21" y2="3"/>
      </svg>
      {source.name}
      <span style={{ color: "var(--color-text-muted)" }}>
        {Math.round(source.similarity_score * 100)}%
      </span>
    </Link>
  );
}

const IconUser = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
);

const IconAI = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <path d="M9 9h.01M15 9h.01M9 15h6"/>
  </svg>
);

const IconSend = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/>
    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);

const IconQuestion = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
);

export default function AnalystPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const checkStatus = useCallback(async () => {
    if (isDemoMode()) { setStatusLoading(false); return; }
    const token = getToken();
    if (!token) { router.push("/login"); return; }
    try {
      const data = await apiFetch<ServiceStatus>("/analyst/status");
      setStatus(data);
      if (!data.available) setError("KI-Service nicht verfügbar. Backend prüfen.");
    } catch {
      // Service offline — kein Fehler anzeigen, Badge zeigt Status
    } finally {
      setStatusLoading(false);
    }
  }, [router]);

  useEffect(() => { checkStatus(); }, [checkStatus]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(question: string) {
    if (!question.trim() || loading) return;
    if (isDemoMode()) {
      setError("KI-Analyse ist im Demo-Modus nicht verfügbar.");
      return;
    }
    if (!getToken()) { router.push("/login"); return; }

    setError(null);
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: question, sources: [] }]);
    setInput("");

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const data = await apiFetch<{ answer: string; sources: Source[] }>("/analyst/ask", {
        method: "POST",
        body: JSON.stringify({ question, conversation_history: history }),
      });
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer, sources: data.sources ?? [] }]);
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes("401")) { router.push("/login"); return; }
      const msg = err instanceof Error ? err.message : "Unbekannter Fehler";
      setMessages((prev) => prev.slice(0, -1));
      setError(msg);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  const isAvailable = !isDemoMode() && status?.available === true;

  return (
    <div className="chatLayout">

      {/* Header */}
      <header className="pageHeader" style={{ marginBottom: 0, flexShrink: 0 }}>
        <div>
          <h1 className="h1">KI-Analyst</h1>
          <p className="muted">Fragen zu Kooperativen, Röstereien und Sourcing-Strategien</p>
        </div>
        <div className="pageActions">
          {statusLoading && (
            <span className="chatStatusBadge">
              <span className="chatStatusDotOffline chatStatusDot" />
              Verbindet...
            </span>
          )}
          {!statusLoading && status?.available && (
            <span className="chatStatusBadge">
              <span className="chatStatusDot" />
              {PROVIDER_LABELS[status.provider] ?? status.provider}
              {" · "}
              <span style={{ color: "var(--color-text)" }}>{status.model}</span>
            </span>
          )}
          {!statusLoading && !status?.available && !isDemoMode() && (
            <span className="chatStatusBadge">
              <span className="chatStatusDotOffline chatStatusDot" />
              Offline
            </span>
          )}
          {messages.length > 0 && (
            <button
              className="btn"
              onClick={() => { setMessages([]); setError(null); }}
            >
              Verlauf leeren
            </button>
          )}
        </div>
      </header>

      {/* Error */}
      {error && (
        <ErrorPanel message={error} onRetry={checkStatus} compact />
      )}

      {/* Chat Panel */}
      <div className="panel chatPanel">

        {/* Messages */}
        <div className="chatMessages">
          {messages.length === 0 && !error ? (
            <div className="chatExamples">
              <EmptyState
                icon={<IconAI />}
                title="Bereit für Ihre Fragen"
                text="Stellen Sie eine Frage über Kooperativen, Röstereien oder Sourcing — oder wählen Sie ein Beispiel."
              />
              <div className="chatExampleList">
                {EXAMPLES.map((q) => (
                  <button
                    key={q}
                    className="chatExampleBtn"
                    onClick={() => send(q)}
                    disabled={!isAvailable || loading}
                  >
                    <IconQuestion />
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <div key={i} className={`chatMsgRow${msg.role === "user" ? " chatMsgRowUser" : ""}`}>
                  <div className={`chatAvatar ${msg.role === "user" ? "chatAvatarUser" : "chatAvatarAi"}`}>
                    {msg.role === "user" ? <IconUser /> : <IconAI />}
                  </div>
                  <div className="chatBubble">
                    <div className={`chatBubbleInner ${msg.role === "user" ? "chatBubbleUser" : "chatBubbleAi"}`}>
                      {msg.content}
                    </div>
                    {msg.sources.length > 0 && (
                      <div className="chatSources">
                        <span className="muted" style={{ fontSize: "var(--font-size-xs)" }}>Quellen:</span>
                        {msg.sources.map((s, j) => <SourceChip key={j} source={s} />)}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="chatMsgRow">
                  <div className="chatAvatar chatAvatarAi"><IconAI /></div>
                  <div className="chatBubble">
                    <div className="chatBubbleInner chatBubbleAi">
                      <TypingIndicator />
                    </div>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="chatInputBar">
          <form
            className="chatInputRow"
            onSubmit={(e) => { e.preventDefault(); send(input); }}
          >
            <div className="chatInputWrap">
              <input
                ref={inputRef}
                className="input"
                placeholder={isAvailable ? "Frage stellen..." : "KI-Service nicht verfügbar"}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading || !isAvailable}
                maxLength={MAX_LEN}
                style={{ paddingRight: input.length > 0 ? "var(--space-12)" : undefined }}
              />
              {input.length > 0 && (
                <span className="chatInputCounter">
                  {input.length}/{MAX_LEN}
                </span>
              )}
            </div>
            <button
              type="submit"
              className="btn btnPrimary"
              disabled={!input.trim() || loading || !isAvailable}
            >
              <IconSend />
              Senden
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}


interface Source {
  entity_type: string;
  entity_id: number;
  name: string;
  similarity_score: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources: Source[];
}

interface ServiceStatus {
  available: boolean;
  provider: string;
  model: string;
  embedding_provider: string;
  embedding_model: string;
}

const EXAMPLE_QUESTIONS = [
  "Welche Kooperativen in Cajamarca haben Fair Trade Zertifizierung?",
  "Vergleiche Röstereien in München nach Bewertung.",
  "Was sind die besten Regionen für Specialty Coffee in Peru?",
  "Zeige mir alle Bio-zertifizierten Kooperativen mit Score über 80.",
];

const PROVIDER_LABELS: Record<string, string> = {
  ollama: "Ollama (lokal)",
  openai: "OpenAI",
  groq: "Groq",
};

function TypingIndicator() {
  return (
    <div style={{ display: "flex", gap: 4, alignItems: "center", padding: "4px 0" }}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "var(--color-text-muted)",
            animation: `typingDot 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

function SourceChip({ source }: { source: Source }) {
  const href = source.entity_type === "cooperative"
    ? `/cooperatives/${source.entity_id}`
    : source.entity_type === "roaster"
    ? `/roasters/${source.entity_id}`
    : "#";
  const pct = Math.round(source.similarity_score * 100);

  return (
    <Link
      href={href}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-2)",
        padding: "3px 10px",
        borderRadius: "var(--radius-full)",
        border: "1px solid var(--color-border-strong)",
        background: "var(--color-bg-subtle)",
        fontSize: "var(--font-size-xs)",
        color: "var(--color-text-secondary)",
        textDecoration: "none",
        transition: "background var(--transition-fast)",
      }}
    >
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
      </svg>
      {source.name}
      <span style={{ color: "var(--color-text-muted)" }}>{pct}%</span>
    </Link>
  );
}

export default function AnalystPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const checkStatus = useCallback(async () => {
    if (isDemoMode()) { setStatusLoading(false); return; }
    const token = getToken();
    if (!token) { router.push("/login"); return; }

    try {
      const data = await apiFetch<ServiceStatus>("/analyst/status");
      setServiceStatus(data);
      if (!data.available) {
        setError(getProviderError(data.provider));
      }
    } catch {
      setError("Verbindung zum KI-Service fehlgeschlagen.");
    } finally {
      setStatusLoading(false);
    }
  }, [router]);

  useEffect(() => { checkStatus(); }, [checkStatus]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function getProviderError(provider: string): string {
    if (provider === "ollama") return "Ollama ist nicht gestartet. Starte Ollama: ollama serve && ollama pull llama3.1:8b";
    if (provider === "openai") return "OPENAI_API_KEY ist nicht konfiguriert.";
    if (provider === "groq") return "GROQ_API_KEY ist nicht konfiguriert.";
    return "KI-Analyst ist derzeit nicht verfügbar.";
  }

  async function sendMessage(question: string) {
    if (!question.trim() || loading) return;
    if (isDemoMode()) {
      setError("KI-Analyse ist im Demo-Modus nicht verfügbar. Bitte Backend starten und einloggen.");
      return;
    }

    const token = getToken();
    if (!token) { router.push("/login"); return; }

    setError(null);
    setLoading(true);
    const userMsg: Message = { role: "user", content: question, sources: [] };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const data = await apiFetch<{ answer: string; sources: Source[] }>("/analyst/ask", {
        method: "POST",
        body: JSON.stringify({ question, conversation_history: history }),
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources ?? [] },
      ]);
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes("401")) { router.push("/login"); return; }
      const msg = err instanceof Error && err.message.includes("503")
        ? "KI-Service nicht verfügbar. Bitte Backend prüfen."
        : err instanceof Error ? err.message : "Unbekannter Fehler";
      setMessages((prev) => prev.slice(0, -1));
      setError(msg);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  const isAvailable = !isDemoMode() && serviceStatus?.available;
  const showExamples = messages.length === 0;

  return (
    <>
      {/* Keyframe für Typing-Dots — einmalig im Head */}
      <style>{`@keyframes typingDot { 0%,60%,100%{opacity:.3;transform:scale(.8)} 30%{opacity:1;transform:scale(1)} }`}</style>

      <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - var(--topbar-height, 56px) - var(--space-10))", gap: "var(--space-4)" }}>

        {/* Header */}
        <div className="pageHeader" style={{ marginBottom: 0, flexShrink: 0 }}>
          <div>
            <div className="h1">KI-Analyst</div>
            <div className="muted">
              Stellen Sie Fragen über Kooperativen, Röstereien und Sourcing-Strategien
            </div>
          </div>
          <div className="pageActions">
            {serviceStatus?.available && (
              <span className="badge badgeInfo" style={{ fontSize: "var(--font-size-xs)" }}>
                {PROVIDER_LABELS[serviceStatus.provider] ?? serviceStatus.provider}
                {" · "}{serviceStatus.model}
              </span>
            )}
            {statusLoading && (
              <span className="badge" style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)" }}>
                Verbinde...
              </span>
            )}
          </div>
        </div>

        {/* Error */}
        {error && <ErrorPanel message={error} onRetry={checkStatus} compact style={{ flexShrink: 0 }} />}

        {/* Chat-Bereich */}
        <div className="panel" style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", padding: 0 }}>

          {/* Nachrichtenliste */}
          <div style={{ flex: 1, overflowY: "auto", padding: "var(--space-5)" }}>
            {showExamples && !error ? (
              <div style={{ height: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                <EmptyState
                  icon={
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                  }
                  title="Bereit für Ihre Fragen"
                  text="Stellen Sie eine Frage über Kooperativen, Röstereien, Preise oder Sourcing — oder wählen Sie ein Beispiel."
                />
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)", maxWidth: 560, margin: "0 auto", width: "100%", paddingBottom: "var(--space-4)" }}>
                  {EXAMPLE_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      className="btn"
                      style={{ textAlign: "left", justifyContent: "flex-start", padding: "var(--space-3) var(--space-4)" }}
                      onClick={() => sendMessage(q)}
                      disabled={!isAvailable || loading}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, color: "var(--color-text-muted)" }}>
                        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4m0-4h.01"/>
                      </svg>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: "flex",
                      gap: "var(--space-3)",
                      flexDirection: msg.role === "user" ? "row-reverse" : "row",
                      alignItems: "flex-start",
                    }}
                  >
                    {/* Avatar */}
                    <div style={{
                      width: 32,
                      height: 32,
                      borderRadius: "var(--radius-md)",
                      background: msg.role === "user" ? "var(--color-primary)" : "var(--color-accent-subtle)",
                      border: `1px solid ${msg.role === "user" ? "transparent" : "var(--color-border-strong)"}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      color: msg.role === "user" ? "var(--color-primary-text)" : "var(--color-accent)",
                    }}>
                      {msg.role === "user" ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                        </svg>
                      ) : (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-1H1a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 10 4a2 2 0 0 1 2-2z"/>
                        </svg>
                      )}
                    </div>

                    {/* Bubble */}
                    <div style={{
                      maxWidth: "72%",
                      display: "flex",
                      flexDirection: "column",
                      gap: "var(--space-2)",
                    }}>
                      <div style={{
                        padding: "var(--space-3) var(--space-4)",
                        borderRadius: msg.role === "user"
                          ? "var(--radius-lg) var(--radius-sm) var(--radius-lg) var(--radius-lg)"
                          : "var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg)",
                        background: msg.role === "user"
                          ? "var(--color-primary)"
                          : "var(--color-bg-subtle)",
                        border: msg.role === "user"
                          ? "none"
                          : "1px solid var(--color-border)",
                        color: msg.role === "user"
                          ? "var(--color-primary-text)"
                          : "var(--color-text)",
                        fontSize: "var(--font-size-base)",
                        lineHeight: "var(--line-height-relaxed)",
                        whiteSpace: "pre-wrap",
                      }}>
                        {msg.content}
                      </div>

                      {/* Quellen */}
                      {msg.sources.length > 0 && (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)", paddingLeft: "var(--space-1)" }}>
                          <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", alignSelf: "center" }}>
                            Quellen:
                          </span>
                          {msg.sources.map((s, i) => <SourceChip key={i} source={s} />)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {/* Typing-Indikator */}
                {loading && (
                  <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "flex-start" }}>
                    <div style={{
                      width: 32, height: 32, borderRadius: "var(--radius-md)",
                      background: "var(--color-accent-subtle)",
                      border: "1px solid var(--color-border-strong)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      color: "var(--color-accent)", flexShrink: 0,
                    }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-1H1a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 10 4a2 2 0 0 1 2-2z"/>
                      </svg>
                    </div>
                    <div style={{
                      padding: "var(--space-3) var(--space-4)",
                      borderRadius: "var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg)",
                      background: "var(--color-bg-subtle)",
                      border: "1px solid var(--color-border)",
                    }}>
                      <TypingIndicator />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input-Leiste */}
          <div style={{
            borderTop: "1px solid var(--color-border)",
            padding: "var(--space-3) var(--space-4)",
            background: "var(--color-surface)",
            flexShrink: 0,
          }}>
            <form
              onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
              style={{ display: "flex", gap: "var(--space-2)", alignItems: "flex-end" }}
            >
              <div style={{ flex: 1, position: "relative" }}>
                <input
                  ref={inputRef}
                  className="input"
                  style={{ paddingRight: "var(--space-10)" }}
                  placeholder={isAvailable ? "Frage stellen..." : "KI-Service nicht verfügbar"}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading || !isAvailable}
                  maxLength={MAX_QUESTION_LENGTH}
                />
                {input.length > 0 && (
                  <span style={{
                    position: "absolute", right: "var(--space-3)", top: "50%",
                    transform: "translateY(-50%)",
                    fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)",
                    fontVariantNumeric: "tabular-nums",
                  }}>
                    {input.length}/{MAX_QUESTION_LENGTH}
                  </span>
                )}
              </div>
              <button
                type="submit"
                className="btn btnPrimary"
                disabled={!input.trim() || loading || !isAvailable}
                style={{ flexShrink: 0 }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
                Senden
              </button>
            </form>
            {messages.length > 0 && (
              <div style={{ marginTop: "var(--space-2)", display: "flex", justifyContent: "flex-end" }}>
                <button
                  className="btn"
                  style={{ fontSize: "var(--font-size-xs)", padding: "3px 10px", color: "var(--color-text-muted)" }}
                  onClick={() => { setMessages([]); setError(null); }}
                >
                  Verlauf leeren
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
