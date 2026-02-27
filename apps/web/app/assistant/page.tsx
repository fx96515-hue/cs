"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getToken, apiBaseUrl } from "../../lib/api";

const MAX_MESSAGE_LENGTH = 1000;

interface Source {
  entity_type: string;
  entity_id: number;
  name: string;
  similarity_score: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  streaming?: boolean;
}

interface ServiceStatus {
  available: boolean;
  enabled: boolean;
  provider: string;
  model: string;
}

const EXAMPLE_QUESTIONS = [
  "Welche Kooperativen in Cajamarca haben Fair Trade Zertifizierung?",
  "Vergleiche Röstereien mit Peru-Fokus",
  "Was sind aktuelle News zu Kaffee-Märkten?",
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const router = useRouter();

  const checkStatus = useCallback(async () => {
    try {
      const token = getToken();
      if (!token) {
        router.push("/login");
        return;
      }
      const res = await fetch(`${apiBaseUrl()}/assistant/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        router.push("/login");
        return;
      }
      const data: ServiceStatus = await res.json();
      setServiceStatus(data);
      if (!data.enabled) {
        setError("Assistant Chat ist deaktiviert.");
      } else if (!data.available) {
        setError(getProviderError(data.provider));
      }
    } catch {
      setServiceStatus(null);
      setError("Fehler beim Verbinden mit dem Service");
    }
  }, [router]);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function getProviderError(provider: string): string {
    switch (provider) {
      case "ollama":
        return "Ollama ist nicht gestartet. Führe `ollama serve` aus und lade ein Modell: `ollama pull llama3.1:8b`";
      case "openai":
        return "OPENAI_API_KEY ist nicht konfiguriert";
      case "groq":
        return "GROQ_API_KEY ist nicht konfiguriert";
      default:
        return "KI-Assistant ist derzeit nicht verfügbar.";
    }
  }

  function getProviderBadge(): string {
    if (!serviceStatus) return "";
    switch (serviceStatus.provider) {
      case "ollama": return "🦙 Ollama";
      case "openai": return "🤖 OpenAI";
      case "groq":   return "⚡ Groq";
      default:       return serviceStatus.provider;
    }
  }

  function getEntityLink(source: Source): string {
    if (source.entity_type === "cooperative") return `/cooperatives/${source.entity_id}`;
    if (source.entity_type === "roaster")     return `/roasters/${source.entity_id}`;
    return "#";
  }

  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return;

    setError(null);
    setLoading(true);
    setInput("");

    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);

    // Placeholder for streaming assistant message
    const assistantIdx = messages.length + 1;
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", streaming: true },
    ]);

    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const res = await fetch(`${apiBaseUrl()}/assistant/chat`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: question, session_id: sessionId }),
        signal: ctrl.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unbekannter Fehler" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("Kein Stream erhalten");

      const decoder = new TextDecoder();
      let buffer = "";
      let finalSources: Source[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (!payload) continue;

          try {
            const event = JSON.parse(payload);

            if (event.type === "session") {
              setSessionId(event.session_id);
            } else if (event.type === "chunk") {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === "assistant") {
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + event.content,
                  };
                }
                return updated;
              });
            } else if (event.type === "done") {
              finalSources = event.sources ?? [];
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === "assistant") {
                  updated[updated.length - 1] = {
                    ...last,
                    streaming: false,
                    sources: finalSources,
                  };
                }
                return updated;
              });
            } else if (event.type === "error") {
              throw new Error(event.message);
            }
          } catch (parseErr) {
            if (parseErr instanceof SyntaxError) continue;
            throw parseErr;
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      const msg =
        err instanceof Error ? err.message : "Fehler beim Senden der Nachricht.";
      // Remove the placeholder assistant message
      setMessages((prev) => prev.slice(0, -1));
      setError(msg);
    } finally {
      setLoading(false);
      abortRef.current = null;
    }

    void assistantIdx; // suppress unused variable warning
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleStop = () => {
    abortRef.current?.abort();
    setLoading(false);
  };

  const handleNewSession = () => {
    setSessionId(null);
    setMessages([]);
    setError(null);
  };

  const isReady = serviceStatus?.enabled && serviceStatus?.available;

  return (
    <div className="assistant-container">
      <div className="assistant-header">
        <div className="header-row">
          <div>
            <h1>💬 KI-Assistant</h1>
            <p className="muted">
              Interaktiver Chatbot mit Zugriff auf Kooperativen, Röstereien und News
            </p>
          </div>
          <div className="header-actions">
            {sessionId && (
              <button className="btn-secondary" onClick={handleNewSession}>
                Neues Gespräch
              </button>
            )}
            {serviceStatus?.available && (
              <span className="provider-badge">{getProviderBadge()}</span>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Fehler:</strong> {error}
        </div>
      )}

      <div className="chat-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🤖</div>
            <h2>Willkommen beim KI-Assistant!</h2>
            <p className="muted">Stellen Sie eine Frage oder wählen Sie ein Beispiel:</p>
            <div className="example-questions">
              {EXAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  className="example-button"
                  onClick={() => sendMessage(q)}
                  disabled={loading || !isReady}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-avatar">
              {msg.role === "user" ? "👤" : "🤖"}
            </div>
            <div className="message-content">
              <div className="message-text">
                {msg.content}
                {msg.streaming && <span className="cursor">▋</span>}
              </div>
              {!msg.streaming && msg.sources && msg.sources.length > 0 && (
                <div className="message-sources">
                  <strong>Quellen:</strong>
                  <ul>
                    {msg.sources.map((src, i) => (
                      <li key={i}>
                        <Link href={getEntityLink(src)}>
                          {src.name} (ID: {src.entity_id})
                        </Link>{" "}
                        <span className="similarity">
                          {(src.similarity_score * 100).toFixed(0)}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="input-field"
          placeholder="Stellen Sie eine Frage..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || !isReady}
          maxLength={MAX_MESSAGE_LENGTH}
        />
        {loading ? (
          <button type="button" className="btn-stop" onClick={handleStop}>
            ⏹ Stop
          </button>
        ) : (
          <button
            type="submit"
            className="btn-send"
            disabled={!input.trim() || !isReady}
          >
            Senden
          </button>
        )}
      </form>

      <style jsx>{`
        .assistant-container {
          max-width: 1000px;
          margin: 0 auto;
          padding: 2rem;
          height: calc(100vh - 4rem);
          display: flex;
          flex-direction: column;
        }
        .assistant-header {
          margin-bottom: 1.5rem;
        }
        .header-row {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
        }
        .header-actions {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          flex-shrink: 0;
        }
        h1 {
          margin: 0 0 0.25rem;
          color: var(--coffee-dark, #3e2723);
        }
        .provider-badge {
          padding: 0.35rem 0.75rem;
          background: var(--coffee-light, #efebe9);
          border: 1px solid var(--coffee-medium, #8d6e63);
          border-radius: 16px;
          font-size: 0.85rem;
          color: var(--coffee-dark, #5d4037);
        }
        .btn-secondary {
          padding: 0.4rem 0.9rem;
          background: white;
          border: 1px solid var(--coffee-medium, #8d6e63);
          border-radius: 6px;
          font-size: 0.85rem;
          cursor: pointer;
          color: var(--coffee-dark, #5d4037);
        }
        .btn-secondary:hover {
          background: var(--coffee-light, #efebe9);
        }
        .alert {
          padding: 0.9rem 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          background: #fee;
          border: 1px solid #fcc;
          color: #c33;
          font-size: 0.9rem;
        }
        .chat-area {
          flex: 1;
          overflow-y: auto;
          background: #fafafa;
          border-radius: 12px;
          padding: 1.5rem;
          margin-bottom: 1rem;
        }
        .empty-state {
          text-align: center;
          padding: 3rem 1rem;
        }
        .empty-icon {
          font-size: 4rem;
          margin-bottom: 1rem;
        }
        .empty-state h2 {
          color: var(--coffee-dark, #3e2723);
          margin-bottom: 0.5rem;
        }
        .example-questions {
          margin-top: 2rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          max-width: 600px;
          margin-left: auto;
          margin-right: auto;
        }
        .example-button {
          padding: 0.9rem 1rem;
          background: white;
          border: 2px solid var(--coffee-medium, #8d6e63);
          border-radius: 8px;
          color: var(--coffee-dark, #3e2723);
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.2s;
          text-align: left;
        }
        .example-button:hover:not(:disabled) {
          background: var(--coffee-light, #efebe9);
          transform: translateY(-2px);
        }
        .example-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .message {
          display: flex;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }
        .message-user {
          flex-direction: row-reverse;
        }
        .message-avatar {
          font-size: 1.75rem;
          width: 38px;
          height: 38px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .message-content {
          max-width: 72%;
          padding: 1rem;
          border-radius: 12px;
          background: white;
          box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        .message-user .message-content {
          background: var(--coffee-light, #efebe9);
        }
        .message-text {
          white-space: pre-wrap;
          line-height: 1.6;
          color: var(--coffee-dark, #3e2723);
          min-height: 1.2em;
        }
        .cursor {
          animation: blink 1s step-end infinite;
          color: var(--coffee-medium, #8d6e63);
        }
        @keyframes blink {
          50% { opacity: 0; }
        }
        .message-sources {
          margin-top: 0.9rem;
          padding-top: 0.9rem;
          border-top: 1px solid #e0e0e0;
          font-size: 0.88rem;
        }
        .message-sources strong {
          color: var(--coffee-dark, #5d4037);
        }
        .message-sources ul {
          margin: 0.4rem 0 0;
          padding-left: 1.25rem;
        }
        .message-sources li {
          margin-bottom: 0.2rem;
        }
        .message-sources a {
          color: var(--coffee-medium, #8d6e63);
          text-decoration: none;
        }
        .message-sources a:hover {
          text-decoration: underline;
        }
        .similarity {
          color: #888;
          font-size: 0.82rem;
        }
        .input-form {
          display: flex;
          gap: 0.75rem;
        }
        .input-field {
          flex: 1;
          padding: 0.9rem 1rem;
          border: 2px solid var(--coffee-medium, #8d6e63);
          border-radius: 8px;
          font-size: 1rem;
        }
        .input-field:focus {
          outline: none;
          border-color: var(--coffee-dark, #5d4037);
        }
        .input-field:disabled {
          background: #f5f5f5;
          cursor: not-allowed;
        }
        .btn-send {
          padding: 0.9rem 1.75rem;
          background: var(--coffee-dark, #5d4037);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
        }
        .btn-send:hover:not(:disabled) {
          background: #4e342e;
        }
        .btn-send:disabled {
          background: #ccc;
          cursor: not-allowed;
        }
        .btn-stop {
          padding: 0.9rem 1.25rem;
          background: #e53935;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
        }
        .btn-stop:hover {
          background: #c62828;
        }
        .muted {
          color: #666;
          margin: 0;
        }
      `}</style>
    </div>
  );
}
