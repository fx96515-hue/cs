"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Report = {
  id: number;
  kind: string;
  title?: string | null;
  report_at: string;
  markdown: string;
  payload?: any;
};

export default function ReportDetailPage() {
  const params = useParams();
  const id = useMemo(() => String(params?.id || ""), [params]);
  const [report, setReport] = useState<Report | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [showPayload, setShowPayload] = useState(false);

  useEffect(() => {
    if (!id) return;
    apiFetch<Report>(`/reports/${id}`)
      .then(setReport)
      .catch((e) => setErr(e.message));
  }, [id]);

  return (
    <div>
      <h1>{report?.title || `Report ${id}`}</h1>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      {report ? (
        <>
          <div style={{ fontSize: 12, color: "#555", marginBottom: 12 }}>
            {new Date(report.report_at).toLocaleString()} — {report.kind}
          </div>

          <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 12 }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.markdown}</ReactMarkdown>
          </div>

          <div style={{ marginTop: 16 }}>
            <button
              onClick={() => setShowPayload((v) => !v)}
              style={{
                padding: "6px 10px",
                borderRadius: 8,
                border: "1px solid #eee",
                background: "white",
                cursor: "pointer",
              }}
            >
              {showPayload ? "Payload ausblenden" : "Payload anzeigen"}
            </button>
            {showPayload && (
              <pre
                style={{
                  marginTop: 8,
                  padding: 12,
                  background: "#fafafa",
                  border: "1px solid #eee",
                  borderRadius: 12,
                  overflowX: "auto",
                }}
              >
                {JSON.stringify(report.payload, null, 2)}
              </pre>
            )}
          </div>
        </>
      ) : (
        <div>Loading…</div>
      )}
    </div>
  );
}
