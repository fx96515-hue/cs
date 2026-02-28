"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, getToken } from "../../lib/api";

// Constants
const MAX_QUESTION_LENGTH = 1000; // Must match backend RAGQuestion.question max_length

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

interface Source {
  entity_type: string;
  entity_id: number;
  name: string;
  similarity_score: number;
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
  "Vergleiche Röstereien in München nach Bewertung",
  "Was sind die besten Regionen für Specialty Coffee in Peru?",
];

export default function AnalystPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(
    null
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const checkServiceStatus = useCallback(async () => {
    try {
      const token = getToken();
      if (!token) {
        router.push("/login");
        return;
      }

      const data: ServiceStatus = await apiFetch<ServiceStatus>("/analyst/status");
      setServiceStatus(data);
      if (!data.available) {
        setError(getProviderErrorMessage(data.provider));
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.message?.includes("401")) {
        router.push("/login");
        return;
      }
      setServiceStatus(null);
      setError("Fehler beim Verbinden mit dem Service");
    }
  }, [router]);

  useEffect(() => {
    checkServiceStatus();
  }, [checkServiceStatus]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const getProviderErrorMessage = (provider: string): string => {
    switch (provider) {
      case "ollama":
        return "Ollama ist nicht gestartet. Starte Ollama mit: `ollama serve` und lade ein Modell: `ollama pull llama3.1:8b`";
      case "openai":
        return "OPENAI_API_KEY ist nicht konfiguriert";
      case "groq":
        return "GROQ_API_KEY ist nicht konfiguriert";
      default:
        return "KI-Analyst ist derzeit nicht verfügbar.";
    }
  };

  const getProviderBadge = (): string => {
    if (!serviceStatus) return "";
    switch (serviceStatus.provider) {
      case "ollama":
        return "🦙 Powered by Ollama";
      case "openai":
        return "🤖 Powered by OpenAI";
      case "groq":
        return "⚡ Powered by Groq";
      default:
        return "";
    }
  };

  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return;

    setError(null);
    setLoading(true);

    const userMessage: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const token = getToken();
      if (!token) {
        router.push("/login");
        return;
      }

      const conversationHistory = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const data = await apiFetch<{
        answer: string;
        sources?: Source[];
      }>(
        "/analyst/ask",
        {
          method: "POST",
          body: JSON.stringify({
            question: question,
            conversation_history: conversationHistory,
          }),
        }
      );

      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      if (err instanceof Error && err.message?.includes("401")) {
        router.push("/login");
        return;
      }
      
      const errorMessage = err instanceof Error && err.message?.includes("503") 
        ? "Service nicht verfügbar." 
        : "Fehler beim Senden der Nachricht.";
      setMessages((prev) => prev.slice(0, -1));
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleExampleClick = (question: string) => {
    sendMessage(question);
  };

  const getEntityLink = (source: Source) => {
    if (source.entity_type === "cooperative") {
      return `/cooperatives/${source.entity_id}`;
    } else if (source.entity_type === "roaster") {
      return `/roasters/${source.entity_id}`;
    }
    return "#";
  };

  return (
    <div className="analyst-container">
      <div className="analyst-header">
        <h1>🤖 KI-Analyst</h1>
        <p className="muted">
          Stellen Sie Fragen über Kooperativen, Röstereien und Sourcing
        </p>
        {serviceStatus && serviceStatus.available && (
          <div className="provider-badge">{getProviderBadge()}</div>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Fehler:</strong> {error}
        </div>
      )}

      <div className="analyst-chat">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h2>Willkommen beim KI-Analysten!</h2>
            <p className="muted">Stellen Sie eine Frage oder wählen Sie ein Beispiel:</p>
            <div className="example-questions">
              {EXAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  className="example-button"
                  onClick={() => handleExampleClick(q)}
                  disabled={loading || !serviceStatus?.available}
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
              <div className="message-text">{msg.content}</div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="message-sources">
                  <strong>Quellen:</strong>
                  <ul>
                    {msg.sources.map((source, i) => (
                      <li key={i}>
                        <Link href={getEntityLink(source)}>
                          {source.name} (ID: {source.entity_id})
                        </Link>{" "}
                        <span className="similarity-score">
                          {(source.similarity_score * 100).toFixed(0)}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="loading-spinner">
                <div className="spinner"></div>
                <span>Denke nach...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="analyst-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="analyst-input"
          placeholder="Stellen Sie eine Frage..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading || !serviceStatus?.available}
          maxLength={MAX_QUESTION_LENGTH}
        />
        <button
          type="submit"
          className="analyst-send-button"
          disabled={!input.trim() || loading || !serviceStatus?.available}
        >
          {loading ? "..." : "Senden"}
        </button>
      </form>

      <style jsx>{`
        .analyst-container {
          max-width: 1000px;
          margin: 0 auto;
          padding: 2rem;
          height: calc(100vh - 4rem);
          display: flex;
          flex-direction: column;
        }

        .analyst-header {
          margin-bottom: 1.5rem;
        }

        .analyst-header h1 {
          margin: 0 0 0.5rem 0;
          color: var(--coffee-dark, #3e2723);
        }

        .provider-badge {
          display: inline-block;
          padding: 0.4rem 0.8rem;
          background: var(--coffee-light, #efebe9);
          border: 1px solid var(--coffee-medium, #8d6e63);
          border-radius: 16px;
          font-size: 0.85rem;
          color: var(--coffee-dark, #5d4037);
          margin-top: 0.5rem;
        }

        .alert {
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          background-color: #fee;
          border: 1px solid #fcc;
          color: #c33;
        }

        .analyst-chat {
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
          padding: 1rem;
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
          border-color: var(--coffee-dark, #5d4037);
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
          font-size: 2rem;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .message-content {
          max-width: 70%;
          padding: 1rem;
          border-radius: 12px;
          background: white;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .message-user .message-content {
          background: var(--coffee-light, #efebe9);
        }

        .message-text {
          white-space: pre-wrap;
          line-height: 1.6;
          color: var(--coffee-dark, #3e2723);
        }

        .message-sources {
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e0e0e0;
          font-size: 0.9rem;
        }

        .message-sources strong {
          color: var(--coffee-dark, #5d4037);
        }

        .message-sources ul {
          margin: 0.5rem 0 0 0;
          padding-left: 1.5rem;
        }

        .message-sources li {
          margin-bottom: 0.25rem;
        }

        .message-sources a {
          color: var(--coffee-medium, #8d6e63);
          text-decoration: none;
        }

        .message-sources a:hover {
          text-decoration: underline;
        }

        .similarity-score {
          color: #666;
          font-size: 0.85rem;
        }

        .loading-spinner {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          color: #666;
        }

        .spinner {
          width: 20px;
          height: 20px;
          border: 3px solid #f3f3f3;
          border-top: 3px solid var(--coffee-medium, #8d6e63);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }

        .analyst-input-form {
          display: flex;
          gap: 0.75rem;
        }

        .analyst-input {
          flex: 1;
          padding: 1rem;
          border: 2px solid var(--coffee-medium, #8d6e63);
          border-radius: 8px;
          font-size: 1rem;
        }

        .analyst-input:focus {
          outline: none;
          border-color: var(--coffee-dark, #5d4037);
        }

        .analyst-input:disabled {
          background: #f5f5f5;
          cursor: not-allowed;
        }

        .analyst-send-button {
          padding: 1rem 2rem;
          background: var(--coffee-dark, #5d4037);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
        }

        .analyst-send-button:hover:not(:disabled) {
          background: var(--coffee-darker, #4e342e);
        }

        .analyst-send-button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .muted {
          color: #666;
        }
      `}</style>
    </div>
  );
}
