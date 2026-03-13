"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";
import DataQualityMini from "../components/DataQualityMini";

/* ============================================================
   REPORTS - ENTERPRISE VIEW
   ============================================================ */

type Report = {
  id: number;
  kind: string;
  title: string | null;
  report_at: string;
};

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiFetch<Report[]>("/reports?limit=50")
      .then(setReports)
      .catch((e) => setErr(e?.message ?? String(e)))
      .finally(() => setLoading(false));
  }, []);

  const getKindBadge = (kind: string): { className: string; label: string } => {
    const map: Record<string, { className: string; label: string }> = {
      daily: { className: "badgeInfo", label: "Taeglich" },
      weekly: { className: "badge", label: "Woechentlich" },
      monthly: { className: "badge", label: "Monatlich" },
      system: { className: "badgeWarn", label: "System" },
      quality: { className: "badgeOk", label: "Qualitaet" },
    };
    return map[kind] || { className: "badge", label: kind };
  };

  return (
    <div className="page">
      <div className="content">
        {/* Page Header */}
        <header className="pageHeader">
          <div className="pageHeaderContent">
            <h1 className="h1">Berichte</h1>
            <p className="subtitle">
              Generierte Tages-, Wochen- und Systemreports - neueste zuerst
            </p>
          </div>
          <div className="pageHeaderActions">
            <a 
              className="btn" 
              href="http://prom.localhost" 
              target="_blank" 
              rel="noreferrer"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
              Prometheus
            </a>
          </div>
        </header>

        {/* Error Alert */}
        {err && (
          <div className="alert bad" style={{ marginBottom: "var(--space-6)" }}>
            <span>{err}</span>
          </div>
        )}

        {/* Reports List */}
        <div className="panel">
          <div className="panelHeader">
            <h2 className="panelTitle">Alle Berichte</h2>
            <span className="badge">{reports.length} Eintraege</span>
          </div>

          {loading ? (
            <div className="panelBody">
              <div className="loading">
                <div className="spinner"></div>
              </div>
            </div>
          ) : reports.length === 0 ? (
            <div className="panelBody">
              <div className="emptyState">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.3, marginBottom: "var(--space-4)" }}>
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                <h3 className="h4">Keine Berichte vorhanden</h3>
                <p className="subtitle">
                  Es wurden noch keine Berichte generiert.
                </p>
              </div>
            </div>
          ) : (
            <div className="list">
              {reports.map((report) => {
                const kindBadge = getKindBadge(report.kind);
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
                        <Badge>{report.kind}</Badge>
                      </div>
                    </div>
                    <span className={`badge ${kindBadge.className}`}>
                      {kindBadge.label}
                    </span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        {/* Data Quality Widget */}
        <div style={{ marginTop: "var(--space-6)" }}>
          <DataQualityMini title="Datenqualitaet (Reports)" limit={10} />
        </div>
      </div>
    </div>
  );
}
