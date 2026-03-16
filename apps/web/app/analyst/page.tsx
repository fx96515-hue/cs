// KI-Analyst — Chat-Interface v2 (neu gestaltet, nur CSS-Klassen aus globals.css)
"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, hasAuthSession, isDemoMode } from "../../lib/api";
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
    if (!hasAuthSession()) { router.push("/login"); return; }
    try {
      const data = await apiFetch<ServiceStatus>("/analyst/status");
      setStatus(data);
      if (!data.available) setError("KI-Service nicht verfügbar. Backend prüfen.");
    } catch {
      // Service offline — Badge zeigt Status
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
    if (!hasAuthSession()) { router.push("/login"); return; }

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
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources ?? [] },
      ]);
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
        <div className="pageHeaderContent">
          <h1 className="h1">KI-Analyst</h1>
          <p className="muted">Fragen zu Kooperativen, Röstereien und Sourcing-Strategien</p>
        </div>
        <div className="pageHeaderActions">
          {statusLoading && (
            <span className="chatStatusBadge">
              <span className="chatStatusDot chatStatusDotOffline" />
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
              <span className="chatStatusDot chatStatusDotOffline" />
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
      {error && <ErrorPanel message={error} onRetry={checkStatus} compact />}

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
                <div
                  key={i}
                  className={`chatMsgRow${msg.role === "user" ? " chatMsgRowUser" : ""}`}
                >
                  <div className={`chatAvatar ${msg.role === "user" ? "chatAvatarUser" : "chatAvatarAi"}`}>
                    {msg.role === "user" ? <IconUser /> : <IconAI />}
                  </div>
                  <div className="chatBubble">
                    <div className={`chatBubbleInner ${msg.role === "user" ? "chatBubbleUser" : "chatBubbleAi"}`}>
                      {msg.content}
                    </div>
                    {msg.sources.length > 0 && (
                      <div className="chatSources">
                        <span className="muted" style={{ fontSize: "var(--font-size-xs)" }}>
                          Quellen:
                        </span>
                        {msg.sources.map((s, j) => (
                          <SourceChip key={j} source={s} />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="chatMsgRow">
                  <div className="chatAvatar chatAvatarAi">
                    <IconAI />
                  </div>
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

        {/* Input Bar */}
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
