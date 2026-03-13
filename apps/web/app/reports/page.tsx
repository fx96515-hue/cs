"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, isDemoMode } from "../../lib/api";
import Badge from "../components/Badge";
import DataQualityMini from "../components/DataQualityMini";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { ErrorPanel } from "../components/AlertError";
import { toErrorMessage } from "../utils/error";

type Report = {
  id: number;
  kind: string;
  title: string | null;
  report_at: string;
};

const KIND_MAP: Record<string, { tone: "good" | "warn" | "neutral" | "info"; label: string }> = {
  daily:   { tone: "info",    label: "Täglich" },
  weekly:  { tone: "neutral", label: "Wöchentlich" },
  monthly: { tone: "neutral", label: "Monatlich" },
  system:  { tone: "warn",    label: "System" },
  quality: { tone: "good",    label: "Qualität" },
};

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    if (isDemoMode()) { setLoading(false); return; }
    setLoading(true);
    setErr(null);
    try {
      const data = await apiFetch<Report[]>("/reports?limit=50");
      setReports(Array.isArray(data) ? data : []);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="content">
      <div className="pageHeader">
        <div>
          <div className="h1">Berichte</div>
          <div className="muted">Generierte Tages-, Wochen- und Systemreports — neueste zuerst.</div>
        </div>
        <div className="pageActions">
          <a
            className="btn"
            href="http://prom.localhost"
            target="_blank"
            rel="noreferrer"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
            Prometheus
          </a>
        </div>
      </div>

      {err && <ErrorPanel message={err} onRetry={load} />}

      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Alle Berichte</div>
          <span className="badge">{reports.length} Einträge</span>
        </div>

        {loading ? (
          <SkeletonRows rows={5} cols={3} />
        ) : reports.length === 0 ? (
          <EmptyState
            icon={
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            }
            title="Keine Berichte vorhanden"
            text="Es wurden noch keine Berichte generiert."
          />
        ) : (
          <div className="list">
            {reports.map((report) => {
              const kind = KIND_MAP[report.kind] ?? { tone: "neutral" as const, label: report.kind };
              return (
                <Link
                  key={report.id}
                  href={`/reports/${report.id}`}
                  className="listItem"
                  style={{ textDecoration: "none" }}
                >
                  <div className="listMain">
                    <div className="listTitle">
                      {report.title || `Report #${report.id}`}
                    </div>
                    <div className="listMeta">
                      <span>{new Date(report.report_at).toLocaleString("de-DE")}</span>
                      <span className="dot">·</span>
                      <Badge tone={kind.tone}>{kind.label}</Badge>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      <div style={{ marginTop: "var(--space-5)" }}>
        <DataQualityMini title="Datenqualität (Reports)" limit={10} />
      </div>
    </div>
  );
}
