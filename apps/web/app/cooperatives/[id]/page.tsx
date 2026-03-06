"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import Badge from "../../components/Badge";
import { DataQualityFlag } from "../../types";

type Cooperative = {
  id: number;
  name: string;
  country?: string | null;
  region?: string | null;
  region_id?: number | null;
  website?: string | null;
  sca_score?: number | null;
  notes?: string | null;
  deleted_at?: string | null;
};

export default function CooperativeDetailsPage() {
  const params = useParams();
  const id = Number(params?.id);
  const router = useRouter();

  const [data, setData] = useState<Cooperative | null>(null);
  const [form, setForm] = useState<Partial<Cooperative>>({});
  const [saving, setSaving] = useState(false);
  const [flags, setFlags] = useState<DataQualityFlag[]>([]);
  const [qualityBusy, setQualityBusy] = useState(false);
  const [regions, setRegions] = useState<{ id: number; name: string; country: string }[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const [d, f, r] = await Promise.all([
          apiFetch<Cooperative>(`/cooperatives/${id}?include_deleted=true`),
          apiFetch<DataQualityFlag[]>(
            `/data-quality/flags?entity_type=cooperative&entity_id=${id}`,
          ),
          apiFetch<{ id: number; name: string; country: string }[]>(`/regions?limit=1000`),
        ]);
        setData(d);
        setFlags(f);
        setRegions(r);
        setForm({
          name: d.name,
          country: d.country ?? "",
          region: d.region ?? "",
          region_id: d.region_id ?? undefined,
          website: d.website ?? "",
          sca_score: d.sca_score ?? undefined,
          notes: d.notes ?? "",
        });
      } catch (e: any) {
        setErr(e?.message ?? String(e));
      }
    })();
  }, [id]);

  async function resolveFlag(flagId: number) {
    setQualityBusy(true);
    try {
      await apiFetch(`/data-quality/flags/${flagId}/resolve`, { method: "POST" });
      const f = await apiFetch<DataQualityFlag[]>(
        `/data-quality/flags?entity_type=cooperative&entity_id=${id}`,
      );
      setFlags(f);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setQualityBusy(false);
    }
  }

  async function recomputeFlags() {
    setQualityBusy(true);
    try {
      await apiFetch(`/data-quality/recompute/cooperative/${id}`, { method: "POST" });
      const f = await apiFetch<DataQualityFlag[]>(
        `/data-quality/flags?entity_type=cooperative&entity_id=${id}`,
      );
      setFlags(f);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setQualityBusy(false);
    }
  }

  async function save() {
    setMsg(null);
    setErr(null);
    setSaving(true);
    try {
      const payload: any = {
        name: (form.name ?? "").toString(),
        country: (form.country ?? "").toString() || null,
        region: (form.region ?? "").toString() || null,
        region_id: form.region_id ? Number(form.region_id) : null,
        website: (form.website ?? "").toString() || null,
        sca_score:
          form.sca_score === undefined ||
          form.sca_score === null ||
          form.sca_score === ("" as any)
            ? null
            : Number(form.sca_score),
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

  async function archive() {
    setErr(null);
    setMsg(null);
    if (!confirm("Kooperative archivieren?")) return;
    try {
      await apiFetch(`/cooperatives/${id}`, { method: "DELETE" });
      router.push("/cooperatives");
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  async function restore() {
    setErr(null);
    setMsg(null);
    try {
      const restored = await apiFetch<Cooperative>(`/cooperatives/${id}/restore`, {
        method: "POST",
      });
      setData(restored);
      setMsg("Wiederhergestellt.");
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  if (!data && !err) {
    return (
      <div className="page">
        <div className="panel">Lade...</div>
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
          {data?.deleted_at ? (
            <button className="btn btnPrimary" onClick={restore}>
              Wiederherstellen
            </button>
          ) : (
            <button className="btn" onClick={archive}>
              Archivieren
            </button>
          )}
          {data?.website ? (
            <a
              className="btn"
              href={data.website.startsWith("http") ? data.website : `https://${data.website}`}
              target="_blank"
              rel="noreferrer"
            >
              Website oeffnen
            </a>
          ) : null}
        </div>
      </div>

      {msg ? <div className="ok">{msg}</div> : null}
      {err ? <div className="error">{err}</div> : null}

      {data?.deleted_at ? (
        <div className="alert bad">
          <div className="alertTitle">Archiviert</div>
          <div className="alertText">Diese Kooperative ist archiviert und nicht aktiv.</div>
        </div>
      ) : null}

      <div className="grid2">
        <div className="panel">
          <div className="panelTitle">Stammdaten</div>
          <div className="form">
            <label>
              <div className="label">Name</div>
              <input
                className="input"
                value={(form.name ?? "") as string}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </label>

            <div className="row gap">
              <label style={{ flex: 1 }}>
                <div className="label">Land</div>
                <input
                  className="input"
                  value={(form.country ?? "") as string}
                  onChange={(e) => setForm({ ...form, country: e.target.value })}
                />
              </label>
              <label style={{ flex: 1 }}>
                <div className="label">Region</div>
                <input
                  className="input"
                  value={(form.region ?? "") as string}
                  onChange={(e) => setForm({ ...form, region: e.target.value })}
                />
              </label>
            </div>

            <label>
              <div className="label">Region (kanonisch)</div>
              <select
                className="input"
                value={form.region_id ?? ""}
                onChange={(e) =>
                  setForm({ ...form, region_id: e.target.value ? Number(e.target.value) : null })
                }
              >
                <option value="">-</option>
                {regions.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.country})
                  </option>
                ))}
              </select>
            </label>

            <label>
              <div className="label">Website</div>
              <input
                className="input"
                value={(form.website ?? "") as string}
                onChange={(e) => setForm({ ...form, website: e.target.value })}
                placeholder="https://"
              />
            </label>

            <label>
              <div className="label">SCA Score</div>
              <input
                className="input"
                type="number"
                step="0.1"
                value={(form.sca_score ?? "") as any}
                onChange={(e) => setForm({ ...form, sca_score: e.target.value as any })}
              />
            </label>

            <label>
              <div className="label">Notizen</div>
              <textarea
                className="textarea"
                value={(form.notes ?? "") as string}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                rows={6}
              />
            </label>

            <div className="row gap">
              <button className="btn primary" onClick={save} disabled={saving}>
                {saving ? "Speichere..." : "Speichern"}
              </button>
              <Link className="btn" href="/ops">
                Enrichment anstossen
              </Link>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panelTitle">Status</div>
          <div className="muted" style={{ marginBottom: 10 }}>
            (Automatisch gefuellt durch Worker - Market/News/Discovery)
          </div>

          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="muted">Website</div>
            {data?.website ? <Badge tone="good">ok</Badge> : <Badge tone="warn">fehlend</Badge>}
          </div>

          <div className="row" style={{ justifyContent: "space-between", marginTop: 10 }}>
            <div className="muted">SCA</div>
            {data?.sca_score ? <Badge tone="good">{data.sca_score}</Badge> : <Badge>-</Badge>}
          </div>

          <div className="divider" />
          <div className="muted">Naechste Schritte</div>
          <ul className="list">
            <li>Website normalisieren (http/https) - dann Enrichment starten.</li>
            <li>Alias/Region ergaenzen - bessere Treffer im Radar.</li>
            <li>Evidence/Web-Extracts pruefen und ggf. handverifizieren.</li>
          </ul>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 14 }}>
        <div className="rowBetween" style={{ marginBottom: 10 }}>
          <div>
            <div className="panelTitle">Datenqualitaet</div>
            <div className="muted">Offene Flags fuer diese Kooperative.</div>
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
