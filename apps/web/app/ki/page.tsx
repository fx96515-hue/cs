'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  toolsUsed?: string[]
}

const EXAMPLE_QUESTIONS = [
  { text: 'Welche Kooperativen in Cajamarca haben Fair Trade?', icon: 'search', category: 'Suche' },
  { text: 'Berechne Landed Cost fuer 500kg Specialty nach Hamburg', icon: 'calc', category: 'Kalkulation' },
  { text: 'Wie sind die aktuellen Markttrends fuer Q1?', icon: 'chart', category: 'Analyse' },
  { text: 'ML-Prognose fuer Frachtkosten Callao-Hamburg', icon: 'brain', category: 'ML' },
  { text: 'Wetterbedingungen in Cajamarca fuer die Ernte?', icon: 'cloud', category: 'Wetter' },
  { text: 'Status der Data Pipeline und Datenquellen', icon: 'database', category: 'System' },
]

const QUICK_ACTIONS = [
  { label: 'Kooperativen durchsuchen', prompt: 'Zeige mir alle Kooperativen mit Bio-Zertifizierung', color: '#16a34a' },
  { label: 'Preis-Prognose', prompt: 'Erstelle eine ML-Prognose fuer Specialty-Preise aus Cajamarca', color: '#2563eb' },
  { label: 'Kostenrechner', prompt: 'Berechne die Landed Cost fuer 1000kg Premium-Kaffee von San Martin nach Berlin', color: '#ca8a04' },
  { label: 'Marktanalyse', prompt: 'Analysiere die Markttrends der letzten 3 Monate mit Fokus auf Preise', color: '#7c3aed' },
]

const DEMO_RESPONSE_DELAY_MS = 1000

// Demo responses based on keywords
const DEMO_RESPONSES: Record<string, { response: string; tools: string[] }> = {
  'kooperativen': {
    response: `Ich habe die Datenbank nach Kooperativen durchsucht. Hier sind die Ergebnisse:

**Kooperativen mit Bio/Fair Trade Zertifizierung:**

1. **CENFROCAFE** (Cajamarca)
   - Zertifizierungen: Fair Trade, Bio, Rainforest Alliance
   - Cupping Score: 85.5
   - Mitglieder: 2,500+ Farmer

2. **Sol y Cafe** (Amazonas)
   - Zertifizierungen: Fair Trade, Bio
   - Cupping Score: 84.8
   - Spezialisierung: Single-Origin Specialty

3. **Norandino** (Piura)
   - Zertifizierungen: Fair Trade, Bio, UTZ
   - Cupping Score: 83.9
   - Exportkapazitaet: 15,000 Saecke/Jahr

Moechten Sie mehr Details zu einer bestimmten Kooperative?`,
    tools: ['searchCooperatives']
  },
  'landed cost': {
    response: `**Landed Cost Kalkulation**

Route: Peru (Callao) → Deutschland (Hamburg)
Menge: 1,000 kg Premium-Kaffee

| Position | Betrag |
|----------|--------|
| FOB Preis (Premium @ 6.50 EUR/kg) | EUR 6,500.00 |
| Seefracht (0.45 EUR/kg) | EUR 450.00 |
| Versicherung (1.5%) | EUR 97.50 |
| Handling & Zoll | EUR 150.00 |
| **Gesamt Landed Cost** | **EUR 7,197.50** |
| **Pro Kilogramm** | **EUR 7.20/kg** |

Geschaetzte Lieferzeit: 4-6 Wochen ab Buchung

Die Kalkulation basiert auf aktuellen Marktpreisen und durchschnittlichen Frachtkosten. Bei groesseren Mengen sind Rabatte moeglich.`,
    tools: ['calculateLandedCost']
  },
  'markttrend': {
    response: `**Markttrend-Analyse Q1 2026**

📈 **Preisentwicklung**
- Richtung: Aufwaerts (+15.2% YTD)
- Haupttreiber: Brasilianische Duerre, steigende Asien-Nachfrage, USD-Schwaeche
- Ausblick: Preise bleiben voraussichtlich hoch bis Q3 2026

📦 **Angebot**
- Status: Angespannt
- Peru Prognose: 4.2 Mio. Saecke
- Globale Lagerbestaende unter 5-Jahres-Durchschnitt
- Engpaesse: Containerknappheit, Hafenverzoegerungen Callao

🌍 **Nachfrage**
- Wachstum: +4.2% YoY
- Top-Maerkte: Deutschland (+6%), USA (+3%), Japan (+5%)
- Specialty-Segment waechst 12% schneller als Commodity

Die Marktlage ist guenstig fuer Produzenten. Empfehlung: Langfristige Vertraege sichern.`,
    tools: ['analyzeMarketTrends']
  },
  'ml': {
    response: `**ML-Prognose: Frachtkosten**

🤖 Model: FreightCostPredictor v2.1
📍 Route: Callao → Hamburg

**Prognose:**
- Geschaetzte Kosten: EUR 2,450 - 2,680 / Container
- Konfidenz: 87%

**Einflussfaktoren:**
- Fuel Price Index: +12% YoY (negativ)
- Hafenauslastung: Moderat (neutral)
- Saisonale Nachfrage: Hoch Q1 (negativ)
- Wetter-Verzoegerungsrisiko: Gering (positiv)

**Model-Genauigkeit:** 92% (letzte 30 Tage)

Die ML-Prognose basiert auf 15 Features inkl. Echtzeitdaten von AIS Shipping und historischen Frachtkosten.`,
    tools: ['getMLPrediction', 'getDataPipelineStatus']
  },
  'wetter': {
    response: `**Wetterbedingungen Cajamarca, Peru**

🌡️ **Aktuelle Bedingungen:**
- Temperatur: 18°C (optimal fuer Kaffee)
- Luftfeuchtigkeit: 72%
- Niederschlag letzte 7 Tage: 45mm

📊 **Agrarmetriken:**
- Bodenfeuchtigkeit: 68% (gut)
- Frost-Risiko: 0% (kein Risiko)
- Duerre-Stress-Index: 0.15 (niedrig)

🌱 **Ernte-Prognose:**
- Timing: Optimal (Haupternte Mai-August)
- Qualitaetsaussichten: Sehr gut
- Schaedlingsrisiko: Gering

Die Wetterbedingungen sind ideal fuer die kommende Ernte. Keine negativen Auswirkungen auf Qualitaet oder Ertrag erwartet.`,
    tools: ['getWeatherForecast']
  },
  'pipeline': {
    response: `**Data Pipeline Status**

✅ **Gesamtstatus:** 16/17 Quellen online

| Quelle | Status | Letzte Sync | Records |
|--------|--------|-------------|---------|
| Yahoo Finance | 🟢 Online | 09:00 | 15,420 |
| ECB FX Rates | 🟢 Online | 08:30 | 8,920 |
| OpenMeteo Weather | 🟢 Online | 06:00 | 45,600 |
| NewsAPI | 🟢 Online | 07:15 | 2,340 |
| AIS Shipping | 🟡 Degraded | 05:45 | 12,800 |
| INEI Peru Stats | 🟢 Online | 00:00 | 890 |

⚠️ **Hinweis:** AIS Shipping zeigt erhoehte Latenz. Team ist informiert.

Naechste geplante Sync: Alle Quellen in 15 Minuten.`,
    tools: ['getDataPipelineStatus']
  },
  'default': {
    response: `Ich verstehe Ihre Anfrage. Als KI-Assistent fuer CoffeeStudio kann ich Ihnen bei folgenden Themen helfen:

- **Kooperativen-Suche**: Finden Sie passende Kaffee-Kooperativen nach Region, Zertifizierung oder Qualitaet
- **Landed Cost Berechnung**: Kalkulieren Sie Gesamtkosten fuer Kaffeeimporte
- **Marktanalyse**: Aktuelle Trends, Preise und Prognosen
- **ML-Prognosen**: Fracht- und Preisvorhersagen basierend auf 50+ Features
- **Wetterdaten**: Anbaubedingungen in Peru
- **System-Status**: Data Pipeline und Datenquellen-Monitoring

Wie kann ich Ihnen weiterhelfen?`,
    tools: []
  }
}

function getIcon(type: string) {
  switch (type) {
    case 'search': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    case 'calc': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="8" y2="10"/><line x1="12" y1="10" x2="12" y2="10"/><line x1="16" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="8" y2="14"/><line x1="12" y1="14" x2="12" y2="14"/><line x1="16" y1="14" x2="16" y2="14"/><line x1="8" y1="18" x2="16" y2="18"/></svg>
    case 'chart': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
    case 'brain': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/></svg>
    case 'cloud': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>
    case 'database': return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
    default: return null
  }
}

function getDemoResponse(input: string): { response: string; tools: string[] } {
  const lower = input.toLowerCase()
  if (lower.includes('kooperativ') || lower.includes('bio') || lower.includes('fair trade')) {
    return DEMO_RESPONSES['kooperativen']
  }
  if (lower.includes('landed') || lower.includes('cost') || lower.includes('kosten') || lower.includes('kalkul')) {
    return DEMO_RESPONSES['landed cost']
  }
  if (lower.includes('markt') || lower.includes('trend') || lower.includes('preis') && lower.includes('analys')) {
    return DEMO_RESPONSES['markttrend']
  }
  if (lower.includes('ml') || lower.includes('prognose') || lower.includes('vorhersage') || lower.includes('fracht')) {
    return DEMO_RESPONSES['ml']
  }
  if (lower.includes('wetter') || lower.includes('ernte') || lower.includes('klima')) {
    return DEMO_RESPONSES['wetter']
  }
  if (lower.includes('pipeline') || lower.includes('status') || lower.includes('datenquelle') || lower.includes('system')) {
    return DEMO_RESPONSES['pipeline']
  }
  return DEMO_RESPONSES['default']
}

export default function KIPage() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messageIdRef = useRef(0)

  const nextMessageId = () => {
    messageIdRef.current += 1
    return messageIdRef.current.toString()
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    
    const userMessage: Message = {
      id: nextMessageId(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // Simulate AI response with demo data
    const demo = getDemoResponse(input)
    
    // Simulate typing delay
    await new Promise(resolve => setTimeout(resolve, DEMO_RESPONSE_DELAY_MS))

    const assistantMessage: Message = {
      id: nextMessageId(),
      role: 'assistant',
      content: demo.response,
      timestamp: new Date(),
      toolsUsed: demo.tools
    }
    
    setMessages(prev => [...prev, assistantMessage])
    setIsLoading(false)
  }

  const handleExample = (question: string) => {
    if (isLoading) return
    setInput(question)
    // Auto-submit
    const userMessage: Message = {
      id: nextMessageId(),
      role: 'user',
      content: question,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    const demo = getDemoResponse(question)
    
    setTimeout(() => {
      const assistantMessage: Message = {
        id: nextMessageId(),
        role: 'assistant',
        content: demo.response,
        timestamp: new Date(),
        toolsUsed: demo.tools
      }
      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)
      setInput('')
    }, DEMO_RESPONSE_DELAY_MS)
  }

  const clearChat = () => {
    setMessages([])
    setInput('')
  }

  return (
    <div className="content" style={{ height: 'calc(100vh - 80px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header className="pageHeader" style={{ flexShrink: 0 }}>
        <div>
          <h1 className="h1">KI-Assistent</h1>
          <p className="muted">Intelligente Suche und Analyse fuer Kaffee-Sourcing</p>
        </div>
        <div className="pageActions">
          <span className="badge badgeInfo" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              background: 'var(--color-info)',
            }} />
            Demo-Modus
          </span>
          {messages.length > 0 && (
            <button className="btn" onClick={clearChat}>
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
                  Dies ist eine Demo-Version mit simulierten Antworten.
                </p>
              </div>

              {/* Quick Actions */}
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 'var(--space-3)',
                width: '100%',
                maxWidth: 600,
                marginBottom: 'var(--space-4)'
              }}>
                {QUICK_ACTIONS.map((action, i) => (
                  <button
                    key={i}
                    onClick={() => handleExample(action.prompt)}
                    disabled={isLoading}
                    style={{
                      padding: 'var(--space-4)',
                      background: `${action.color}10`,
                      border: `1px solid ${action.color}30`,
                      borderRadius: 'var(--radius-lg)',
                      textAlign: 'center',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      opacity: isLoading ? 0.5 : 1,
                      transition: 'all 0.15s ease',
                      fontSize: 'var(--font-size-sm)',
                      fontWeight: 500,
                      color: action.color,
                    }}
                    onMouseEnter={(e) => {
                      if (!isLoading) {
                        e.currentTarget.style.background = `${action.color}20`
                        e.currentTarget.style.transform = 'translateY(-2px)'
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = `${action.color}10`
                      e.currentTarget.style.transform = 'translateY(0)'
                    }}
                  >
                    {action.label}
                  </button>
                ))}
              </div>

              {/* Example Questions */}
              <div style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 'var(--space-2)',
                width: '100%',
                maxWidth: 600
              }}>
                <span className="muted" style={{ fontSize: 'var(--font-size-xs)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Oder stelle eine Frage
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-2)' }}>
                  {EXAMPLE_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleExample(q.text)}
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
                        color: 'var(--color-text)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-2)',
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
                      <span style={{ color: 'var(--color-text-muted)', flexShrink: 0 }}>{getIcon(q.icon)}</span>
                      <span style={{ flex: 1 }}>{q.text}</span>
                      <span style={{ 
                        fontSize: 'var(--font-size-xs)', 
                        color: 'var(--color-text-muted)',
                        background: 'var(--color-bg-muted)',
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-sm)',
                      }}>
                        {q.category}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {messages.map((message) => {
                const isUser = message.role === 'user'

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
                        {message.content}
                      </div>

                      {/* Tool Results */}
                      {message.toolsUsed && message.toolsUsed.length > 0 && (
                        <div style={{
                          padding: 'var(--space-2) var(--space-3)',
                          background: 'var(--color-info-subtle)',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--color-info-border)',
                          fontSize: 'var(--font-size-xs)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--space-2)',
                        }}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-info)" strokeWidth="2">
                            <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                          </svg>
                          <span style={{ color: 'var(--color-info)' }}>
                            Tools: {message.toolsUsed.join(', ')}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}

              {/* Loading Indicator */}
              {isLoading && (
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
                    <span className="loadingDot" style={{ animationDelay: '0s' }} />
                    <span className="loadingDot" style={{ animationDelay: '0.16s' }} />
                    <span className="loadingDot" style={{ animationDelay: '0.32s' }} />
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
              className="btn btnPrimary"
              type="submit"
              disabled={isLoading || !input.trim()}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 'var(--space-2)',
                minWidth: 100
              }}
            >
              {isLoading ? (
                <>
                  <span className="loadingDot" style={{ background: 'white', animationDelay: '0s' }} />
                  <span className="loadingDot" style={{ background: 'white', animationDelay: '0.16s' }} />
                  <span className="loadingDot" style={{ background: 'white', animationDelay: '0.32s' }} />
                </>
              ) : (
                <>
                  Senden
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22,2 15,22 11,13 2,9"/>
                  </svg>
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
              Demo-Modus - Antworten sind simuliert
            </span>
            <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
              <Link href="/search" className="muted" style={{ 
                fontSize: 'var(--font-size-xs)', 
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-1)',
              }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                </svg>
                Suche
              </Link>
              <Link href="/analytics" className="muted" style={{ 
                fontSize: 'var(--font-size-xs)', 
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-1)',
              }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
                </svg>
                Analytics
              </Link>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .loadingDot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--color-primary);
          animation: bounce 1.4s infinite ease-in-out both;
        }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}</style>
    </div>
  )
}
