"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import Badge from "../../components/Badge";
import { Breadcrumb } from "../../components/Breadcrumb";
import { useToast } from "../../components/ToastProvider";
import { DataQualityFlag } from "../../types";
import { toErrorMessage } from "../../utils/error";

type Roaster = {
  id: number;
  name: string;
  country?: string | null;
  city?: string | null;
  website?: string | null;
  notes?: string | null;
  deleted_at?: string | null;
};

export default function RoasterDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params?.id);
  const router = useRouter();
  const toast = useToast();
  const [r, setR] = useState<Roaster | null>(null);
  const [saving, setSaving] = useState(false);
  const [flags, setFlags] = useState<DataQualityFlag[]>([]);
  const [qualityBusy, setQualityBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const [d, f] = await Promise.all([
          apiFetch<Roaster>(`/roasters/${id}?include_deleted=true`),
          apiFetch<DataQualityFlag[]>(`/data-quality/flags?entity_type=roaster&entity_id=${id}`),
        ]);
        setR(d);
        setFlags(f);
      } catch (error: unknown) {
        setErr(toErrorMessage(error));
      }
    })();
  }, [id]);

  async function resolveFlag(flagId: number) {
    setQualityBusy(true);
    try {
      await apiFetch(`/data-quality/flags/${flagId}/resolve`, { method: "POST" });
      const f = await apiFetch<DataQualityFlag[]>(
        `/data-quality/flags?entity_type=roaster&entity_id=${id}`,
      );
      setFlags(f);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setQualityBusy(false);
    }
  }

  async function recomputeFlags() {
    setQualityBusy(true);
    try {
      await apiFetch(`/data-quality/recompute/roaster/${id}`, { method: "POST" });
      const f = await apiFetch<DataQualityFlag[]>(
        `/data-quality/flags?entity_type=roaster&entity_id=${id}`,
      );
      setFlags(f);
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setQualityBusy(false);
    }
  }

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
    } catch (error: unknown) {
      setErr(toErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function archive() {
    setErr(null);
    setMsg(null);
    if (!confirm("Rösterei archivieren?")) return;
    try {
      await apiFetch(`/roasters/${id}`, { method: "DELETE" });
      toast.success(`"${r?.name}" wurde archiviert.`);
      router.push("/roasters");
    } catch (error: unknown) {
      toast.error(toErrorMessage(error));
      setErr(toErrorMessage(error));
    }
  }

  async function restore() {
    setErr(null);
    setMsg(null);
    try {
      const restored = await apiFetch<Roaster>(`/roasters/${id}/restore`, { method: "POST" });
      setR(restored);
      toast.success("Rösterei wurde wiederhergestellt.");
      setMsg("Wiederhergestellt.");
    } catch (error: unknown) {
      toast.error(toErrorMessage(error));
      setErr(toErrorMessage(error));
    }
  }

  if (err) {
    return (
      <div className="page">
                <div className="alert bad"><div className="alertText">{err}</div></div>
        <Link className="btn" href="/roasters">
          Zurueck
        </Link>
      </div>
    );
  }

  if (!r) {
    return (
      <div className="page">
        <div className="panel">Lade...</div>
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
      <Breadcrumb items={[
        { label: "Startseite", href: "/dashboard" },
        { label: "Röstereien", href: "/roasters" },
        { label: r.name },
      ]} />
      <div className="pageHeader">
        <div>
          <div className="h1">Rösterei #{r.id}</div>
          <div className="muted">Stammdaten & Notizen</div>
        </div>
        <div className="row gap">
          <Link className="btn" href="/roasters">
            Zur Liste
          </Link>
          {r?.deleted_at ? (
            <button className="btn btnPrimary" onClick={restore}>
              Wiederherstellen
            </button>
          ) : (
            <button className="btn" onClick={archive}>
              Archivieren
            </button>
          )}
          <button className="btn btnPrimary" onClick={save} disabled={saving}>
            {saving ? "Speichere..." : "Speichern"}
          </button>
        </div>
      </div>

          {msg ? <div className="alert ok"><div className="alertText">{msg}</div></div> : null}

      {r?.deleted_at ? (
        <div className="alert bad">
          <div className="alertTitle">Archiviert</div>
          <div className="alertText">Diese Rösterei ist archiviert und nicht aktiv.</div>
        </div>
      ) : null}

      <div className="grid2">
        <div className="panel">
          <div className="panelTitle">Stammdaten</div>
          <div className="form">
            <label className="label">Name</label>
            <input
              className="input"
              value={r.name}
              onChange={(e) => setR({ ...r, name: e.target.value })}
            />

            <label className="label">Stadt</label>
            <input
              className="input"
              value={r.city ?? ""}
              onChange={(e) => setR({ ...r, city: e.target.value })}
            />

            <label className="label">Land</label>
            <input
              className="input"
              value={r.country ?? ""}
              onChange={(e) => setR({ ...r, country: e.target.value })}
            />

            <label className="label">Website</label>
            <input
              className="input"
              value={r.website ?? ""}
              onChange={(e) => setR({ ...r, website: e.target.value })}
            />
            {websiteHref ? (
              <div className="row" style={{ marginTop: 8 }}>
                <a className="link" href={websiteHref} target="_blank" rel="noreferrer">
                  <Badge tone="good">Website oeffnen</Badge>
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
            Tipp: Nutze diese Notizen als CRM-Vorarbeit (Tonality + Anknoepfungspunkte).
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 14 }}>
        <div className="rowBetween" style={{ marginBottom: 10 }}>
          <div>
            <div className="panelTitle">Datenqualitaet</div>
            <div className="muted">Offene Flags fuer diese Rösterei.</div>
          </div>
          <div className="row gap">
            <button className="btn" onClick={recomputeFlags} disabled={qualityBusy}>
              Neu berechnen
            </button>
          </div>
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Feld</th>
                <th>Issue</th>
                <th>Severity</th>
                <th>Aktion</th>
              </tr>
            </thead>
            <tbody>
              {flags.length ? (
                flags.map((flag) => (
                  <tr key={flag.id}>
                    <td>{flag.field_name || "-"}</td>
                    <td>{flag.message || flag.issue_type}</td>
                    <td>
                      <Badge
                        tone={
                          flag.severity === "critical"
                            ? "bad"
                            : flag.severity === "warning"
                              ? "warn"
                              : "neutral"
                        }
                      >
                        {flag.severity}
                      </Badge>
                    </td>
                    <td>
                      <button
                        className="btn"
                        onClick={() => resolveFlag(flag.id)}
                        disabled={qualityBusy}
                      >
                        Resolve
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="muted">
                    Keine offenen Flags.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
