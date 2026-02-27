"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import Badge from "../../components/Badge";

type Cooperative = {
  id: number;
  name: string;
  country?: string | null;
  region?: string | null;
  website?: string | null;
  sca_score?: number | null;
  notes?: string | null;
};

export default function CooperativeDetailsPage() {
  const params = useParams();
  const id = Number(params?.id);

  const [data, setData] = useState<Cooperative | null>(null);
  const [form, setForm] = useState<Partial<Cooperative>>({});
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const d = await apiFetch<Cooperative>(`/cooperatives/${id}`);
        setData(d);
        setForm({
          name: d.name,
          country: d.country ?? "",
          region: d.region ?? "",
          website: d.website ?? "",
          sca_score: d.sca_score ?? undefined,
          notes: d.notes ?? "",
        });
      } catch (e: any) {
        setErr(e?.message ?? String(e));
      }
    })();
  }, [id]);

  async function save() {
    setMsg(null);
    setErr(null);
    setSaving(true);
    try {
      const payload: any = {
        name: (form.name ?? "").toString(),
        country: (form.country ?? "").toString() || null,
        region: (form.region ?? "").toString() || null,
        website: (form.website ?? "").toString() || null,
        sca_score: form.sca_score === undefined || form.sca_score === null || form.sca_score === ("" as any) ? null : Number(form.sca_score),
        notes: (form.notes ?? "").toString() || null,
      };
      const updated = await apiFetch<Cooperative>(`/cooperatives/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      setData(updated);
      setMsg("Gespeichert.");
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setSaving(false);
    }
  }

  if (!data && !err) {
    return (
      <div className="page">
        <div className="panel">Lade…</div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Kooperative #{id}</div>
          <div className="muted">Datenpflege + Website + Enrichment</div>
        </div>
        <div className="row gap">
          <Link className="btn" href="/cooperatives">
            Zur Liste
          </Link>
          {data?.website ? (
            <a className="btn" href={(data.website.startsWith("http") ? data.website : `https://${data.website}`)} target="_blank" rel="noreferrer">
              Website öffnen
            </a>
          ) : null}
        </div>
      </div>

      {msg ? <div className="ok">{msg}</div> : null}
      {err ? <div className="error">{err}</div> : null}

      <div className="grid2">
        <div className="panel">
          <div className="panelTitle">Stammdaten</div>
          <div className="form">
            <label>
              <div className="label">Name</div>
              <input className="input" value={(form.name ?? "") as string} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>

            <div className="row gap">
              <label style={{ flex: 1 }}>
                <div className="label">Land</div>
                <input className="input" value={(form.country ?? "") as string} onChange={(e) => setForm({ ...form, country: e.target.value })} />
              </label>
              <label style={{ flex: 1 }}>
                <div className="label">Region</div>
                <input className="input" value={(form.region ?? "") as string} onChange={(e) => setForm({ ...form, region: e.target.value })} />
              </label>
            </div>

            <label>
              <div className="label">Website</div>
              <input className="input" value={(form.website ?? "") as string} onChange={(e) => setForm({ ...form, website: e.target.value })} placeholder="https://…" />
            </label>

            <label>
              <div className="label">SCA Score</div>
              <input className="input" type="number" step="0.1" value={(form.sca_score ?? "") as any} onChange={(e) => setForm({ ...form, sca_score: e.target.value as any })} />
            </label>

            <label>
              <div className="label">Notizen</div>
              <textarea className="textarea" value={(form.notes ?? "") as string} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={6} />
            </label>

            <div className="row gap">
              <button className="btn primary" onClick={save} disabled={saving}>
                {saving ? "Speichere…" : "Speichern"}
              </button>
              <Link className="btn" href="/ops">
                Enrichment anstoßen
              </Link>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panelTitle">Status</div>
          <div className="muted" style={{ marginBottom: 10 }}>
            (Automatisch gefüllt durch Worker – Market/News/Discovery)
          </div>

          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="muted">Website</div>
            {data?.website ? <Badge tone="good">ok</Badge> : <Badge tone="warn">fehlend</Badge>}
          </div>

          <div className="row" style={{ justifyContent: "space-between", marginTop: 10 }}>
            <div className="muted">SCA</div>
            {data?.sca_score ? <Badge tone="good">{data.sca_score}</Badge> : <Badge>–</Badge>}
          </div>

          <div className="divider" />
          <div className="muted">Nächste Schritte</div>
          <ul className="list">
            <li>Website normalisieren (http/https) – dann Enrichment starten.</li>
            <li>Alias/Region ergänzen → bessere Treffer im Radar.</li>
            <li>Evidence/Web-Extracts prüfen und ggf. handverifizieren.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
