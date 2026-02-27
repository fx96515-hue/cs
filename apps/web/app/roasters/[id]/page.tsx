"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import Badge from "../../components/Badge";

type Roaster = {
  id: number;
  name: string;
  country?: string | null;
  city?: string | null;
  website?: string | null;
  notes?: string | null;
};

export default function RoasterDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const [r, setR] = useState<Roaster | null>(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const d = await apiFetch<Roaster>(`/roasters/${id}`);
        setR(d);
      } catch (e: any) {
        setErr(e?.message ?? String(e));
      }
    })();
  }, [id]);

  async function save() {
    if (!r) return;
    setSaving(true);
    setMsg(null);
    setErr(null);
    try {
      const d = await apiFetch<Roaster>(`/roasters/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: r.name,
          country: r.country,
          city: r.city,
          website: r.website,
          notes: r.notes,
        }),
      });
      setR(d);
      setMsg("Gespeichert.");
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setSaving(false);
    }
  }

  if (err) {
    return (
      <div className="page">
        <div className="error">{err}</div>
        <Link className="btn" href="/roasters">
          Zurück
        </Link>
      </div>
    );
  }

  if (!r) {
    return (
      <div className="page">
        <div className="panel">Lade…</div>
      </div>
    );
  }

  const websiteHref = r.website
    ? r.website.startsWith("http")
      ? r.website
      : `https://${r.website}`
    : null;

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Rösterei #{r.id}</div>
          <div className="muted">Stammdaten & Notizen</div>
        </div>
        <div className="row gap">
          <Link className="btn" href="/roasters">
            Zur Liste
          </Link>
          <button className="btn btnPrimary" onClick={save} disabled={saving}>
            {saving ? "Speichere…" : "Speichern"}
          </button>
        </div>
      </div>

      {msg ? <div className="success">{msg}</div> : null}
      {err ? <div className="error">{err}</div> : null}

      <div className="grid2">
        <div className="panel">
          <div className="panelTitle">Stammdaten</div>
          <div className="form">
            <label className="label">Name</label>
            <input className="input" value={r.name} onChange={(e) => setR({ ...r, name: e.target.value })} />

            <label className="label">Stadt</label>
            <input className="input" value={r.city ?? ""} onChange={(e) => setR({ ...r, city: e.target.value })} />

            <label className="label">Land</label>
            <input className="input" value={r.country ?? ""} onChange={(e) => setR({ ...r, country: e.target.value })} />

            <label className="label">Website</label>
            <input className="input" value={r.website ?? ""} onChange={(e) => setR({ ...r, website: e.target.value })} />
            {websiteHref ? (
              <div className="row" style={{ marginTop: 8 }}>
                <a className="link" href={websiteHref} target="_blank" rel="noreferrer">
                  <Badge tone="good">Website öffnen</Badge>
                </a>
              </div>
            ) : (
              <div className="muted" style={{ marginTop: 8 }}>
                Keine Website hinterlegt.
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panelTitle">Notizen</div>
          <textarea
            className="textarea"
            rows={14}
            value={r.notes ?? ""}
            onChange={(e) => setR({ ...r, notes: e.target.value })}
            placeholder="z.B. Ansprechpartner, Konditionen, Profile, Specialty Fokus, ..."
          />
          <div className="muted" style={{ marginTop: 10 }}>
            Tipp: Nutze diese Notizen als CRM-Vorarbeit (Tonality + Anknüpfungspunkte).
          </div>
        </div>
      </div>
    </div>
  );
}
