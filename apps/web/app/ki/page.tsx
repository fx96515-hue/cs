'use client'

import { useState, useRef, useEffect } from 'react'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import Link from 'next/link'

const EXAMPLE_QUESTIONS = [
  'Welche Kooperativen in Cajamarca haben Fair Trade Zertifizierung?',
  'Finde Roestereien in Berlin mit Peru-Fokus',
  'Wie sind die aktuellen Specialty Coffee Preise?',
  'Wetterbedingungen in Cajamarca fuer die Ernte?',
  'Aktuelle News zu Kaffee-Exporten aus Peru',
]

function getUIMessageText(parts: Array<{ type: string; text?: string }>): string {
  return parts
    .filter((p): p is { type: 'text'; text: string } => p.type === 'text' && typeof p.text === 'string')
    .map((p) => p.text)
    .join('')
}

export default function KIPage() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ api: '/api/ai-chat' }),
  })

  const isLoading = status === 'streaming' || status === 'submitted'

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    sendMessage({ text: input })
    setInput('')
  }

  const handleExample = (question: string) => {
    if (isLoading) return
    sendMessage({ text: question })
  }

  return (
    <div className="page" style={{ height: 'calc(100vh - 80px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header className="pageHeader" style={{ flexShrink: 0 }}>
        <div>
          <h1 className="h1">KI-Assistent</h1>
          <p className="muted">Intelligente Suche und Analyse fuer Kaffee-Sourcing</p>
        </div>
        <div className="pageActions">
          <span className="badge badgeSuccess" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              background: 'var(--color-success)',
              animation: 'pulse 2s infinite'
            }} />
            Vercel AI Gateway
          </span>
          {messages.length > 0 && (
            <button
              className="btn"
              onClick={() => window.location.reload()}
            >
              Neues Gespraech
            </button>
          )}
        </div>
      </header>

      {/* Chat Container */}
      <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* Messages Area */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: 'var(--space-6)',
          background: 'var(--color-bg-subtle)'
        }}>
          {messages.length === 0 ? (
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              gap: 'var(--space-6)'
            }}>
              {/* AI Icon */}
              <div style={{
                width: 80,
                height: 80,
                borderRadius: 'var(--radius-xl)',
                background: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-hover) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 32px rgba(93, 64, 55, 0.2)'
              }}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                  <path d="M9 14v2"/>
                  <path d="M15 14v2"/>
                </svg>
              </div>

              <div>
                <h2 style={{ 
                  fontSize: 'var(--font-size-xl)', 
                  fontWeight: 'var(--font-weight-semibold)',
                  marginBottom: 'var(--space-2)',
                  color: 'var(--color-text)'
                }}>
                  Willkommen beim KI-Assistenten
                </h2>
                <p className="muted" style={{ maxWidth: 400 }}>
                  Stellen Sie Fragen zu Kooperativen, Roestereien, Preisen und Markttrends.
                  Die KI nutzt aktuelle Daten aus dem CoffeeStudio-System.
                </p>
              </div>

              {/* Example Questions */}
              <div style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 'var(--space-2)',
                width: '100%',
                maxWidth: 500
              }}>
                <span className="muted" style={{ fontSize: 'var(--font-size-xs)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Beispielfragen
                </span>
                {EXAMPLE_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleExample(q)}
                    disabled={isLoading}
                    style={{
                      padding: 'var(--space-3) var(--space-4)',
                      background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-lg)',
                      textAlign: 'left',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      opacity: isLoading ? 0.5 : 1,
                      transition: 'all 0.15s ease',
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--color-text)'
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.borderColor = 'var(--color-primary)'
                        e.currentTarget.style.background = 'var(--color-bg-muted)'
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--color-border)'
                      e.currentTarget.style.background = 'var(--color-surface)'
                    }}
                  >
                    <span style={{ color: 'var(--color-primary)', marginRight: 'var(--space-2)' }}>?</span>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {messages.map((message) => {
                const isUser = message.role === 'user'
                const text = getUIMessageText(message.parts as Array<{ type: string; text?: string }>)
                
                // Check for tool results in parts
                const toolParts = message.parts.filter(p => p.type.startsWith('tool-'))

                return (
                  <div
                    key={message.id}
                    style={{
                      display: 'flex',
                      flexDirection: isUser ? 'row-reverse' : 'row',
                      gap: 'var(--space-3)',
                      alignItems: 'flex-start'
                    }}
                  >
                    {/* Avatar */}
                    <div style={{
                      width: 36,
                      height: 36,
                      borderRadius: 'var(--radius-full)',
                      background: isUser ? 'var(--color-bg-muted)' : 'var(--color-primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      {isUser ? (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                          <circle cx="12" cy="7" r="4"/>
                        </svg>
                      ) : (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                          <rect x="3" y="3" width="18" height="18" rx="2"/>
                          <path d="M9 9h.01M15 9h.01M9 15h6"/>
                        </svg>
                      )}
                    </div>

                    {/* Message Bubble */}
                    <div style={{
                      maxWidth: '75%',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-2)'
                    }}>
                      <div style={{
                        padding: 'var(--space-3) var(--space-4)',
                        borderRadius: 'var(--radius-lg)',
                        background: isUser ? 'var(--color-primary)' : 'var(--color-surface)',
                        color: isUser ? 'white' : 'var(--color-text)',
                        border: isUser ? 'none' : '1px solid var(--color-border)',
                        lineHeight: 1.6,
                        whiteSpace: 'pre-wrap'
                      }}>
                        {text}
                        {status === 'streaming' && !isUser && message.id === messages[messages.length - 1]?.id && (
                          <span style={{ 
                            display: 'inline-block',
                            width: 6,
                            height: 16,
                            background: 'var(--color-primary)',
                            marginLeft: 2,
                            animation: 'blink 1s step-end infinite'
                          }} />
                        )}
                      </div>

                      {/* Tool Results */}
                      {toolParts.length > 0 && (
                        <div style={{
                          padding: 'var(--space-3)',
                          background: 'var(--color-bg-muted)',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--color-border)',
                          fontSize: 'var(--font-size-xs)'
                        }}>
                          <span className="muted" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Datenabfrage durchgefuehrt
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}

              {/* Loading Indicator */}
              {isLoading && messages.length > 0 && messages[messages.length - 1]?.role === 'user' && (
                <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start' }}>
                  <div style={{
                    width: 36,
                    height: 36,
                    borderRadius: 'var(--radius-full)',
                    background: 'var(--color-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                      <rect x="3" y="3" width="18" height="18" rx="2"/>
                      <path d="M9 9h.01M15 9h.01M9 15h6"/>
                    </svg>
                  </div>
                  <div style={{
                    padding: 'var(--space-3) var(--space-4)',
                    borderRadius: 'var(--radius-lg)',
                    background: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    display: 'flex',
                    gap: 'var(--space-2)'
                  }}>
                    <span style={{ 
                      width: 8, 
                      height: 8, 
                      borderRadius: '50%', 
                      background: 'var(--color-primary)',
                      animation: 'bounce 1.4s infinite ease-in-out both',
                      animationDelay: '0s'
                    }} />
                    <span style={{ 
                      width: 8, 
                      height: 8, 
                      borderRadius: '50%', 
                      background: 'var(--color-primary)',
                      animation: 'bounce 1.4s infinite ease-in-out both',
                      animationDelay: '0.16s'
                    }} />
                    <span style={{ 
                      width: 8, 
                      height: 8, 
                      borderRadius: '50%', 
                      background: 'var(--color-primary)',
                      animation: 'bounce 1.4s infinite ease-in-out both',
                      animationDelay: '0.32s'
                    }} />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div style={{ 
          padding: 'var(--space-4)',
          borderTop: '1px solid var(--color-border)',
          background: 'var(--color-surface)'
        }}>
          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <input
              className="input"
              style={{ flex: 1 }}
              placeholder="Stellen Sie eine Frage..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              className="btn btnPrimary"
              disabled={!input.trim() || isLoading}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 'var(--space-2)',
                minWidth: 100
              }}
            >
              {isLoading ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
                    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                  </svg>
                  <span>Denkt...</span>
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                  </svg>
                  <span>Senden</span>
                </>
              )}
            </button>
          </form>
          
          <div style={{ 
            marginTop: 'var(--space-3)', 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span className="muted" style={{ fontSize: 'var(--font-size-xs)' }}>
              Powered by GPT-5 Mini via Vercel AI Gateway
            </span>
            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              <Link href="/search" className="muted" style={{ fontSize: 'var(--font-size-xs)', textDecoration: 'none' }}>
                Semantische Suche
              </Link>
              <span className="muted" style={{ fontSize: 'var(--font-size-xs)' }}>|</span>
              <Link href="/analyst" className="muted" style={{ fontSize: 'var(--font-size-xs)', textDecoration: 'none' }}>
                Legacy Analyst
              </Link>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes blink {
          50% { opacity: 0; }
        }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}
