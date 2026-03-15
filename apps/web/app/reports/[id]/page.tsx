"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { apiFetch } from "../../../lib/api";
import Badge from "../../components/Badge";
import { toErrorMessage } from "../../utils/error";

type Report = {
  id: number;
  kind: string;
  title: string | null;
  report_at: string;
  markdown: string;
  payload: unknown;
};

function kindTone(kind: string): "info" | "neutral" | "warn" | "good" {
  if (kind === "daily") return "info";
  if (kind === "system") return "warn";
  if (kind === "quality") return "good";
  return "neutral";
}

export default function ReportDetailPage() {
  const params = useParams();
  const id = useMemo(() => String(params?.id || ""), [params]);
  const [report, setReport] = useState<Report | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [showPayload, setShowPayload] = useState(false);
  const loading = report === null && err === null;

  useEffect(() => {
    if (!id) return;
    apiFetch<Report>(`/reports/${id}`)
      .then(setReport)
      .catch((e: unknown) => setErr(toErrorMessage(e)));
  }, [id]);

  return (
    <div className="content">
      <header className="pageHeader">
        <div>
          <h1 className="h1">{report?.title || `Report #${id}`}</h1>
          <p className="subtitle">Detailansicht des generierten Tages-/Systemberichts.</p>
        </div>
        <div className="pageActions">
          <Link className="btn" href="/reports">Zurueck zu Berichten</Link>
        </div>
      </header>

      {err ? (
        <div className="alert bad">
          <div className="alertText">{err}</div>
        </div>
      ) : null}

      <section className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Metadaten</div>
          {report ? <Badge tone={kindTone(report.kind)}>{report.kind}</Badge> : null}
        </div>
        <div className="panelBody">
          {loading ? (
            <div className="muted">Laedt...</div>
          ) : report ? (
            <div className="row gap" style={{ flexWrap: "wrap" }}>
              <span className="muted">Report-ID: {report.id}</span>
              <span className="muted">Erstellt: {new Date(report.report_at).toLocaleString("de-DE")}</span>
            </div>
          ) : (
            <div className="muted">Kein Bericht gefunden.</div>
          )}
        </div>
      </section>

      <section className="panel" style={{ marginTop: "var(--space-4)" }}>
        <div className="panelHeader">
          <div className="panelTitle">Inhalt</div>
        </div>
        <div className="panelBody">
          {loading ? (
            <div className="muted">Laedt Berichtsinhalt...</div>
          ) : report ? (
            <div className="markdownBody">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.markdown || ""}</ReactMarkdown>
            </div>
          ) : (
            <div className="muted">Keine Inhalte verfuegbar.</div>
          )}
        </div>
      </section>

      <section className="panel" style={{ marginTop: "var(--space-4)" }}>
        <div className="panelHeader">
          <div className="panelTitle">Technische Details</div>
          <button className="btn btnSm" onClick={() => setShowPayload((v) => !v)}>
            {showPayload ? "Payload ausblenden" : "Payload anzeigen"}
          </button>
        </div>
        {showPayload && report ? (
          <div className="panelBody">
            <pre className="codeBox" style={{ maxHeight: 420, overflow: "auto" }}>
              {JSON.stringify(report.payload, null, 2)}
            </pre>
          </div>
        ) : null}
      </section>
    </div>
  );
}
