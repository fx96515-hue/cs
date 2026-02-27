"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

type Report = {
  id: number;
  kind: string;
  title?: string | null;
  report_at: string;
};

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Report[]>("/reports?limit=50").then(setReports).catch((e) => setErr(e.message));
  }, []);

  return (
    <div>
      <div className="pageHeader">
        <div>
          <div className="pageTitle">Berichte</div>
          <div className="pageSubtitle">Generierte Tages-/Systemreports (aus DB) – neueste oben.</div>
        </div>
        <a className="btn" href="http://prom.localhost" target="_blank" rel="noreferrer">
          Prometheus öffnen
        </a>
      </div>

      {err && <div className="alert">{err}</div>}

      <div className="panel">
        {reports.length === 0 ? (
          <div className="muted">Keine Reports vorhanden.</div>
        ) : (
          <div className="list">
            {reports.map((r) => (
              <div key={r.id} className="row">
                <div className="rowMain">
                  <Link className="link" href={`/reports/${r.id}`}>
                    {r.title || `Report #${r.id}`}
                  </Link>
                  <div className="rowSub">
                    {new Date(r.report_at).toLocaleString()} — <Badge>{r.kind}</Badge>
                  </div>
                </div>
                <div className="rowActions">
                  <Link className="btn" href={`/reports/${r.id}`}>
                    öffnen
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
