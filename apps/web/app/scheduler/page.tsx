"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ErrorPanel } from "../components/AlertError";
import Badge from "../components/Badge";
import { EmptyState, SkeletonKpiGrid, SkeletonRows } from "../components/EmptyState";
import { apiFetch } from "../../lib/api";

type JobCategory = "pipeline" | "ml" | "maintenance";

interface ScheduledJob {
  id: string;
  task: string;
  description: string;
  category: JobCategory;
  schedule: string;
  scheduleHuman: string;
  nextRunAt: string;
  enabled: boolean;
  kwargs: Record<string, unknown>;
}

interface SchedulerSummary {
  total: number;
  enabled: number;
  categories: Record<string, number>;
  celery_eager: boolean;
}

interface TaskStatus {
  task_id: string;
  state: string;
  ready: boolean;
  result?: Record<string, unknown> | null;
}

const CATEGORY_INFO: Record<JobCategory, { label: string; tone: "info" | "good" | "warn" }> = {
  pipeline: { label: "Data Pipeline", tone: "info" },
  ml: { label: "ML / Search", tone: "good" },
  maintenance: { label: "Wartung", tone: "warn" },
};

function formatDateTime(value: string) {
  try {
    return new Date(value).toLocaleString("de-DE");
  } catch {
    return value;
  }
}

function formatRelative(value: string) {
  const target = new Date(value).getTime();
  const diffMinutes = Math.round((target - Date.now()) / 60000);
  if (Number.isNaN(diffMinutes)) return "—";
  if (diffMinutes < 0) return "Ueberfaellig";
  if (diffMinutes < 60) return `in ${diffMinutes} Min.`;
  const hours = Math.floor(diffMinutes / 60);
  if (hours < 24) return `in ${hours} Std.`;
  return `in ${Math.floor(hours / 24)} Tagen`;
}

function taskBadgeTone(state: string): "neutral" | "good" | "warn" | "bad" | "info" {
  if (state === "SUCCESS") return "good";
  if (state === "STARTED" || state === "PENDING") return "info";
  if (state === "FAILURE") return "bad";
  return "warn";
}

export default function SchedulerPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [summary, setSummary] = useState<SchedulerSummary | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<"all" | JobCategory>("all");
  const [taskStates, setTaskStates] = useState<Record<string, TaskStatus>>({});
  const [runLoading, setRunLoading] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [jobList, schedulerSummary] = await Promise.all([
        apiFetch<ScheduledJob[]>("/scheduler/jobs"),
        apiFetch<SchedulerSummary>("/scheduler/summary"),
      ]);
      setJobs(jobList);
      setSummary(schedulerSummary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scheduler konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    const pending = Object.entries(taskStates).filter(([, task]) => !task.ready);
    if (pending.length === 0) return;

    const timer = window.setInterval(() => {
      pending.forEach(async ([jobId, task]) => {
        try {
          const next = await apiFetch<TaskStatus>(`/scheduler/tasks/${task.task_id}`);
          setTaskStates((current) => ({ ...current, [jobId]: next }));
        } catch {
          // Keep current state; UI already shows the last known task status.
        }
      });
    }, 2500);

    return () => window.clearInterval(timer);
  }, [taskStates]);

  const filteredJobs = useMemo(() => {
    if (selectedCategory === "all") return jobs;
    return jobs.filter((job) => job.category === selectedCategory);
  }, [jobs, selectedCategory]);

  const upcomingJobs = useMemo(() => {
    return [...jobs]
      .sort((left, right) => new Date(left.nextRunAt).getTime() - new Date(right.nextRunAt).getTime())
      .slice(0, 5);
  }, [jobs]);

  async function runJob(jobId: string) {
    setRunLoading(jobId);
    setError(null);
    try {
      const queued = await apiFetch<{ task_id: string }>(`/scheduler/jobs/${jobId}/run`, {
        method: "POST",
      });
      setTaskStates((current) => ({
        ...current,
        [jobId]: { task_id: queued.task_id, state: "PENDING", ready: false, result: null },
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Job konnte nicht gestartet werden.");
    } finally {
      setRunLoading(null);
    }
  }

  return (
    <div className="page">
      <header className="pageHeader">
        <div>
          <h1 className="h1">Scheduler</h1>
          <p className="muted">Konfigurierte Hintergrundjobs, Kategorien und manuelle Ausloesung.</p>
        </div>
        <div className="pageActions">
          <Link href="/pipeline" className="btn btnSecondary">
            Pipeline
          </Link>
          <button className="btn" onClick={() => void loadData()} disabled={loading} type="button">
            Neu laden
          </button>
        </div>
      </header>

      {error && <ErrorPanel compact message={error} onRetry={() => void loadData()} />}

      {loading ? (
        <SkeletonKpiGrid count={4} />
      ) : (
        <div className="kpiGrid" style={{ marginBottom: "var(--space-5)" }}>
          <div className="kpiCard">
            <div className="kpiLabel">Jobs gesamt</div>
            <div className="kpiValue">{summary?.total ?? 0}</div>
            <div className="kpiMeta">Aus Celery Beat Konfiguration</div>
          </div>
          <div className="kpiCard">
            <div className="kpiLabel">Aktiv</div>
            <div className="kpiValue">{summary?.enabled ?? 0}</div>
            <div className="kpiMeta">Derzeit konfiguriert</div>
          </div>
          <div className="kpiCard">
            <div className="kpiLabel">Pipeline Jobs</div>
            <div className="kpiValue">{summary?.categories.pipeline ?? 0}</div>
            <div className="kpiMeta">Markt, News, Intelligence</div>
          </div>
          <div className="kpiCard">
            <div className="kpiLabel">Ausfuehrungsmodus</div>
            <div className="kpiValue">{summary?.celery_eager ? "Eager" : "Worker"}</div>
            <div className="kpiMeta">Testmodus oder echter Queue-Betrieb</div>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: "var(--space-6)" }}>
        <section className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Geplante Jobs</div>
            <div style={{ display: "flex", gap: "var(--space-2)" }}>
              <button
                className={selectedCategory === "all" ? "btn btnPrimary btnSm" : "btn btnSm"}
                onClick={() => setSelectedCategory("all")}
                type="button"
              >
                Alle
              </button>
              {(Object.keys(CATEGORY_INFO) as JobCategory[]).map((category) => (
                <button
                  key={category}
                  className={selectedCategory === category ? "btn btnPrimary btnSm" : "btn btnSm"}
                  onClick={() => setSelectedCategory(category)}
                  type="button"
                >
                  {CATEGORY_INFO[category].label}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="panelBody">
              <SkeletonRows rows={6} />
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="panelBody">
              <EmptyState title="Keine Jobs fuer diesen Filter" description="Wechseln Sie den Filter oder pruefen Sie die Beat-Konfiguration." />
            </div>
          ) : (
            <div className="tableWrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Job</th>
                    <th>Kategorie</th>
                    <th>Schedule</th>
                    <th>Naechster Lauf</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredJobs.map((job) => {
                    const task = taskStates[job.id];
                    return (
                      <tr key={job.id}>
                        <td>
                          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                            <strong className="mono">{job.id}</strong>
                            <span className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                              {job.description}
                            </span>
                          </div>
                        </td>
                        <td>
                          <Badge tone={CATEGORY_INFO[job.category].tone}>{CATEGORY_INFO[job.category].label}</Badge>
                        </td>
                        <td>
                          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                            <span className="mono">{job.schedule}</span>
                            <span className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                              {job.scheduleHuman}
                            </span>
                          </div>
                        </td>
                        <td>
                          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                            <span>{formatRelative(job.nextRunAt)}</span>
                            <span className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                              {formatDateTime(job.nextRunAt)}
                            </span>
                          </div>
                        </td>
                        <td>
                          {task ? (
                            <Badge tone={taskBadgeTone(task.state)}>{task.state}</Badge>
                          ) : (
                            <Badge tone="neutral">Konfiguriert</Badge>
                          )}
                        </td>
                        <td>
                          <button
                            className="btn btnSm"
                            onClick={() => void runJob(job.id)}
                            disabled={runLoading === job.id}
                            type="button"
                          >
                            {runLoading === job.id ? "Queue..." : "Jetzt starten"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <aside style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <section className="panel">
            <div className="panelHeader">
              <div className="panelTitle">Naechste Ausfuehrungen</div>
            </div>
            <div className="panelBody" style={{ padding: 0 }}>
              {upcomingJobs.map((job, index) => (
                <div
                  key={job.id}
                  style={{
                    padding: "var(--space-3) var(--space-4)",
                    borderBottom: index < upcomingJobs.length - 1 ? "1px solid var(--color-border)" : "none",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--space-2)" }}>
                    <strong className="mono" style={{ fontSize: "var(--font-size-sm)" }}>
                      {job.id}
                    </strong>
                    <Badge tone={CATEGORY_INFO[job.category].tone}>{CATEGORY_INFO[job.category].label}</Badge>
                  </div>
                  <div className="muted" style={{ fontSize: "var(--font-size-sm)", marginTop: "var(--space-1)" }}>
                    {formatRelative(job.nextRunAt)} · {job.scheduleHuman}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <div className="panelTitle">Hinweise</div>
            </div>
            <div className="panelBody" style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
              <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                Die Seite zeigt die aktuelle Celery-Beat-Konfiguration. Laufzeiten und manuelle Starts kommen direkt aus dem Backend.
              </div>
              <div className="muted" style={{ fontSize: "var(--font-size-sm)" }}>
                Schalter fuer Aktivierung oder Cron-Aenderung sind absichtlich nicht hier, weil diese Aenderungen kontrolliert ueber Konfiguration und Deployment erfolgen sollten.
              </div>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
