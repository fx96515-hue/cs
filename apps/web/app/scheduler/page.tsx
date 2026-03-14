"use client"

import { useState } from "react"
import Link from "next/link"
import { isDemoMode } from "../../lib/api"

// Types
interface ScheduledJob {
  id: string
  name: string
  description: string
  schedule: string
  scheduleHuman: string
  category: "pipeline" | "ml" | "report" | "maintenance"
  lastRun: string | null
  lastStatus: "success" | "failed" | "running" | null
  lastDuration: number | null
  nextRun: string
  enabled: boolean
}

// Demo Data - Celery Beat Schedule
const DEMO_JOBS: ScheduledJob[] = [
  {
    id: "job-001",
    name: "coffee_prices_sync",
    description: "Kaffeepreise von Yahoo Finance synchronisieren",
    schedule: "*/15 * * * *",
    scheduleHuman: "Alle 15 Minuten",
    category: "pipeline",
    lastRun: "2026-03-14T09:00:00Z",
    lastStatus: "success",
    lastDuration: 12,
    nextRun: "2026-03-14T09:15:00Z",
    enabled: true,
  },
  {
    id: "job-002",
    name: "fx_rates_sync",
    description: "Wechselkurse von ECB und OANDA abrufen",
    schedule: "0 */1 * * *",
    scheduleHuman: "Stuendlich",
    category: "pipeline",
    lastRun: "2026-03-14T09:00:00Z",
    lastStatus: "success",
    lastDuration: 8,
    nextRun: "2026-03-14T10:00:00Z",
    enabled: true,
  },
  {
    id: "job-003",
    name: "weather_data_sync",
    description: "Wetterdaten fuer Peru Anbauregionen aktualisieren",
    schedule: "0 */6 * * *",
    scheduleHuman: "Alle 6 Stunden",
    category: "pipeline",
    lastRun: "2026-03-14T06:00:00Z",
    lastStatus: "success",
    lastDuration: 45,
    nextRun: "2026-03-14T12:00:00Z",
    enabled: true,
  },
  {
    id: "job-004",
    name: "news_sentiment_sync",
    description: "News und Social Media Sentiment analysieren",
    schedule: "0 */3 * * *",
    scheduleHuman: "Alle 3 Stunden",
    category: "pipeline",
    lastRun: "2026-03-14T09:00:00Z",
    lastStatus: "success",
    lastDuration: 120,
    nextRun: "2026-03-14T12:00:00Z",
    enabled: true,
  },
  {
    id: "job-005",
    name: "shipping_tracking_sync",
    description: "AIS Schiffspositionen und Hafendaten abrufen",
    schedule: "*/30 * * * *",
    scheduleHuman: "Alle 30 Minuten",
    category: "pipeline",
    lastRun: "2026-03-14T08:30:00Z",
    lastStatus: "failed",
    lastDuration: 5,
    nextRun: "2026-03-14T09:30:00Z",
    enabled: true,
  },
  {
    id: "job-006",
    name: "ml_features_compute",
    description: "ML Features fuer alle aktiven Deals berechnen",
    schedule: "0 2 * * *",
    scheduleHuman: "Taeglich um 02:00",
    category: "ml",
    lastRun: "2026-03-14T02:00:00Z",
    lastStatus: "success",
    lastDuration: 340,
    nextRun: "2026-03-15T02:00:00Z",
    enabled: true,
  },
  {
    id: "job-007",
    name: "freight_model_retrain",
    description: "Freight Cost ML Model neu trainieren",
    schedule: "0 3 * * 0",
    scheduleHuman: "Woechentlich (So 03:00)",
    category: "ml",
    lastRun: "2026-03-10T03:00:00Z",
    lastStatus: "success",
    lastDuration: 1820,
    nextRun: "2026-03-17T03:00:00Z",
    enabled: true,
  },
  {
    id: "job-008",
    name: "price_model_retrain",
    description: "Price Forecast ML Model neu trainieren",
    schedule: "0 4 * * 0",
    scheduleHuman: "Woechentlich (So 04:00)",
    category: "ml",
    lastRun: "2026-03-10T04:00:00Z",
    lastStatus: "success",
    lastDuration: 2100,
    nextRun: "2026-03-17T04:00:00Z",
    enabled: true,
  },
  {
    id: "job-009",
    name: "daily_summary_report",
    description: "Taeglichen Zusammenfassungsbericht generieren",
    schedule: "0 6 * * *",
    scheduleHuman: "Taeglich um 06:00",
    category: "report",
    lastRun: "2026-03-14T06:00:00Z",
    lastStatus: "success",
    lastDuration: 25,
    nextRun: "2026-03-15T06:00:00Z",
    enabled: true,
  },
  {
    id: "job-010",
    name: "monthly_analytics_report",
    description: "Monatlichen Analytics-Report erstellen",
    schedule: "0 0 1 * *",
    scheduleHuman: "Monatlich (1. um 00:00)",
    category: "report",
    lastRun: "2026-03-01T00:00:00Z",
    lastStatus: "success",
    lastDuration: 180,
    nextRun: "2026-04-01T00:00:00Z",
    enabled: true,
  },
  {
    id: "job-011",
    name: "data_quality_check",
    description: "Datenqualitaetspruefung durchfuehren",
    schedule: "0 1 * * *",
    scheduleHuman: "Taeglich um 01:00",
    category: "maintenance",
    lastRun: "2026-03-14T01:00:00Z",
    lastStatus: "success",
    lastDuration: 90,
    nextRun: "2026-03-15T01:00:00Z",
    enabled: true,
  },
  {
    id: "job-012",
    name: "db_vacuum_analyze",
    description: "PostgreSQL VACUUM und ANALYZE ausfuehren",
    schedule: "0 5 * * 0",
    scheduleHuman: "Woechentlich (So 05:00)",
    category: "maintenance",
    lastRun: "2026-03-10T05:00:00Z",
    lastStatus: "success",
    lastDuration: 420,
    nextRun: "2026-03-17T05:00:00Z",
    enabled: false,
  },
  {
    id: "job-013",
    name: "cache_cleanup",
    description: "Alte Cache-Eintraege bereinigen",
    schedule: "0 4 * * *",
    scheduleHuman: "Taeglich um 04:00",
    category: "maintenance",
    lastRun: "2026-03-14T04:00:00Z",
    lastStatus: "success",
    lastDuration: 15,
    nextRun: "2026-03-15T04:00:00Z",
    enabled: true,
  },
]

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins < 60) return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
  const hours = Math.floor(mins / 60)
  const remainMins = mins % 60
  return `${hours}h ${remainMins}m`
}

function formatTimeUntil(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 0) return "Ueberfaellig"
  if (diffMins < 60) return `in ${diffMins} Min.`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `in ${diffHours} Std.`
  const diffDays = Math.floor(diffHours / 24)
  return `in ${diffDays} Tagen`
}

function formatLastRun(dateStr: string | null): string {
  if (!dateStr) return "Nie"
  const date = new Date(dateStr)
  return date.toLocaleString("de-DE", { 
    day: "2-digit", 
    month: "2-digit", 
    hour: "2-digit", 
    minute: "2-digit" 
  })
}

const CATEGORY_INFO: Record<string, { label: string; color: string; icon: JSX.Element }> = {
  pipeline: {
    label: "Data Pipeline",
    color: "#2563eb",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
      </svg>
    ),
  },
  ml: {
    label: "ML / AI",
    color: "#7c3aed",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
      </svg>
    ),
  },
  report: {
    label: "Reports",
    color: "#16a34a",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
  },
  maintenance: {
    label: "Wartung",
    color: "#ca8a04",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
      </svg>
    ),
  },
}

export default function SchedulerPage() {
  const [jobs, setJobs] = useState<ScheduledJob[]>(DEMO_JOBS)
  const [categoryFilter, setCategoryFilter] = useState<string>("all")
  const [showDisabled, setShowDisabled] = useState(false)
  const isDemo = isDemoMode()

  const filteredJobs = jobs.filter((job) => {
    if (categoryFilter !== "all" && job.category !== categoryFilter) return false
    if (!showDisabled && !job.enabled) return false
    return true
  })

  const stats = {
    total: jobs.length,
    enabled: jobs.filter((j) => j.enabled).length,
    failed: jobs.filter((j) => j.lastStatus === "failed").length,
    running: jobs.filter((j) => j.lastStatus === "running").length,
  }

  const upcomingJobs = [...jobs]
    .filter((j) => j.enabled)
    .sort((a, b) => new Date(a.nextRun).getTime() - new Date(b.nextRun).getTime())
    .slice(0, 5)

  const toggleJob = (id: string) => {
    setJobs((prev) =>
      prev.map((j) => (j.id === id ? { ...j, enabled: !j.enabled } : j))
    )
  }

  const triggerJob = (id: string) => {
    setJobs((prev) =>
      prev.map((j) =>
        j.id === id
          ? { ...j, lastRun: new Date().toISOString(), lastStatus: "running" as const, lastDuration: null }
          : j
      )
    )
    // Simulate completion after 2 seconds
    setTimeout(() => {
      setJobs((prev) =>
        prev.map((j) =>
          j.id === id && j.lastStatus === "running"
            ? { ...j, lastStatus: "success" as const, lastDuration: Math.floor(Math.random() * 60) + 5 }
            : j
        )
      )
    }, 2000)
  }

  return (
    <div className="page-container">
      {/* Header */}
      <header className="pageHeader">
        <div className="pageHeaderContent">
          <h1 className="h1">Scheduler Dashboard</h1>
          <p className="subtitle">Geplante Jobs und automatische Aufgaben verwalten</p>
        </div>
        <div className="pageHeaderActions">
          <Link href="/pipeline" className="btn btnGhost">
            Data Pipeline
          </Link>
          <Link href="/ops" className="btn btnGhost">
            Systemstatus
          </Link>
        </div>
      </header>

      {/* Stats */}
      <div className="kpiGrid" style={{ marginBottom: "var(--space-6)" }}>
        <div className="kpiCard">
          <span className="cardLabel">Jobs Gesamt</span>
          <span className="cardValue">{stats.total}</span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Aktiv</span>
          <span className="cardValue" style={{ color: "var(--color-success)" }}>{stats.enabled}</span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Fehlgeschlagen</span>
          <span className="cardValue" style={{ color: stats.failed > 0 ? "var(--color-danger)" : undefined }}>
            {stats.failed}
          </span>
        </div>
        <div className="kpiCard">
          <span className="cardLabel">Laufend</span>
          <span className="cardValue" style={{ color: stats.running > 0 ? "var(--color-info)" : undefined }}>
            {stats.running}
          </span>
        </div>
      </div>

      {/* Two Column Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: "var(--space-6)" }}>
        {/* Job List */}
        <section className="panel">
          <div className="panelHeader">
            <h2 className="panelTitle">Scheduled Jobs</h2>
            <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--font-size-sm)" }}>
                <input
                  type="checkbox"
                  checked={showDisabled}
                  onChange={(e) => setShowDisabled(e.target.checked)}
                />
                Deaktivierte anzeigen
              </label>
            </div>
          </div>

          {/* Category Filter */}
          <div style={{ padding: "var(--space-3) var(--space-4)", borderBottom: "1px solid var(--color-border)", display: "flex", gap: "var(--space-2)" }}>
            <button
              className={categoryFilter === "all" ? "btn btnPrimary btnSm" : "btn btnGhost btnSm"}
              onClick={() => setCategoryFilter("all")}
            >
              Alle
            </button>
            {Object.entries(CATEGORY_INFO).map(([key, info]) => (
              <button
                key={key}
                className={categoryFilter === key ? "btn btnPrimary btnSm" : "btn btnGhost btnSm"}
                onClick={() => setCategoryFilter(key)}
                style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}
              >
                {info.icon}
                {info.label}
              </button>
            ))}
          </div>

          {/* Job Table */}
          <div className="tableWrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Job</th>
                  <th>Schedule</th>
                  <th>Letzter Lauf</th>
                  <th>Naechster Lauf</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredJobs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="tableEmpty">Keine Jobs fuer diesen Filter</td>
                  </tr>
                ) : (
                  filteredJobs.map((job) => {
                    const catInfo = CATEGORY_INFO[job.category]
                    return (
                      <tr key={job.id} style={{ opacity: job.enabled ? 1 : 0.5 }}>
                        <td>
                          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                              <span style={{ color: catInfo.color }}>{catInfo.icon}</span>
                              <span className="mono" style={{ fontWeight: 500 }}>{job.name}</span>
                            </div>
                            <span className="muted small">{job.description}</span>
                          </div>
                        </td>
                        <td>
                          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                            <span className="mono small">{job.schedule}</span>
                            <span className="muted small">{job.scheduleHuman}</span>
                          </div>
                        </td>
                        <td>
                          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                            <span className="small">{formatLastRun(job.lastRun)}</span>
                            {job.lastDuration !== null && (
                              <span className="muted small">{formatDuration(job.lastDuration)}</span>
                            )}
                          </div>
                        </td>
                        <td>
                          <span className="small" style={{ color: job.enabled ? "var(--color-text)" : "var(--color-text-muted)" }}>
                            {job.enabled ? formatTimeUntil(job.nextRun) : "Deaktiviert"}
                          </span>
                        </td>
                        <td>
                          {job.lastStatus === "success" && (
                            <span className="badge good">Erfolgreich</span>
                          )}
                          {job.lastStatus === "failed" && (
                            <span className="badge bad">Fehlgeschlagen</span>
                          )}
                          {job.lastStatus === "running" && (
                            <span className="badge neutral" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--color-info)", animation: "pulse 1s infinite" }} />
                              Laeuft
                            </span>
                          )}
                          {job.lastStatus === null && (
                            <span className="badge neutral">Ausstehend</span>
                          )}
                        </td>
                        <td>
                          <div style={{ display: "flex", gap: "var(--space-2)" }}>
                            <button
                              className="btn btnGhost btnSm"
                              onClick={() => triggerJob(job.id)}
                              disabled={!job.enabled || job.lastStatus === "running" || isDemo}
                              title="Jetzt ausfuehren"
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polygon points="5 3 19 12 5 21 5 3"/>
                              </svg>
                            </button>
                            <button
                              className="btn btnGhost btnSm"
                              onClick={() => toggleJob(job.id)}
                              disabled={isDemo}
                              title={job.enabled ? "Deaktivieren" : "Aktivieren"}
                            >
                              {job.enabled ? (
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <rect x="6" y="4" width="4" height="16"/>
                                  <rect x="14" y="4" width="4" height="16"/>
                                </svg>
                              ) : (
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <polygon points="5 3 19 12 5 21 5 3"/>
                                </svg>
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Sidebar */}
        <aside style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          {/* Upcoming Jobs */}
          <section className="panel">
            <div className="panelHeader">
              <h3 className="panelTitle">Naechste Jobs</h3>
            </div>
            <div className="panelBody" style={{ padding: 0 }}>
              {upcomingJobs.map((job, i) => {
                const catInfo = CATEGORY_INFO[job.category]
                return (
                  <div
                    key={job.id}
                    style={{
                      padding: "var(--space-3) var(--space-4)",
                      borderBottom: i < upcomingJobs.length - 1 ? "1px solid var(--color-border)" : "none",
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-3)",
                    }}
                  >
                    <span style={{ color: catInfo.color }}>{catInfo.icon}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="mono small" style={{ fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {job.name}
                      </div>
                      <div className="muted small">{formatTimeUntil(job.nextRun)}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>

          {/* Category Legend */}
          <section className="panel">
            <div className="panelHeader">
              <h3 className="panelTitle">Kategorien</h3>
            </div>
            <div className="panelBody" style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
              {Object.entries(CATEGORY_INFO).map(([key, info]) => {
                const count = jobs.filter((j) => j.category === key && j.enabled).length
                return (
                  <div
                    key={key}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "var(--space-2)",
                      borderRadius: "var(--radius-md)",
                      background: `${info.color}10`,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                      <span style={{ color: info.color }}>{info.icon}</span>
                      <span style={{ fontSize: "var(--font-size-sm)" }}>{info.label}</span>
                    </div>
                    <span className="badge neutral">{count}</span>
                  </div>
                )
              })}
            </div>
          </section>

          {/* Quick Info */}
          <section className="panel">
            <div className="panelHeader">
              <h3 className="panelTitle">Info</h3>
            </div>
            <div className="panelBody">
              <p className="muted small" style={{ marginBottom: "var(--space-2)" }}>
                Jobs werden durch Celery Beat orchestriert und laufen automatisch nach dem definierten Schedule.
              </p>
              <p className="muted small">
                <strong>Cron-Format:</strong> Minute Stunde Tag Monat Wochentag
              </p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}
