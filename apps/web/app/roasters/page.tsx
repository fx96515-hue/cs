"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

type Roaster = {
  id: number;
  name: string;
  country?: string | null;
  city?: string | null;
  website?: string | null;
};

type RoasterList = { items: Roaster[]; total: number };

export default function RoastersPage() {
  const [data, setData] = useState<RoasterList | null>(null);
  const [q, setQ] = useState("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const d = await apiFetch<Roaster[] | RoasterList>("/roasters?limit=200");
        // Backend returns flat list, but we need { items, total } format
        if (Array.isArray(d)) {
          setData({ items: d, total: d.length });
        } else {
          setData(d);
        }
      } catch (e: any) {
        setErr(e?.message ?? String(e));
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    const items = data?.items ?? [];
    const t = q.trim().toLowerCase();
    if (!t) return items;
    return items.filter((r) => `${r.name} ${r.city ?? ""} ${r.country ?? ""}`.toLowerCase().includes(t));
  }, [data, q]);

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Röstereien</div>
          <div className="muted">CRM-Pipeline + Zielkunden</div>
        </div>
        <div className="row gap">
          <input className="input" style={{ width: 320 }} placeholder="Suchen…" value={q} onChange={(e) => setQ(e.target.value)} />
          <Link className="btn" href="/ops">
            Discovery / Seed
          </Link>
        </div>
      </div>

      {err ? <div className="error">{err}</div> : null}

      <div className="panel">
        <div className="panelTitle">
          Treffer: <span className="mono">{filtered.length}</span> (gesamt {data?.total ?? "–"})
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: 80 }}>ID</th>
                <th>Name</th>
                <th>Ort</th>
                <th>Land</th>
                <th>Website</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.id}</td>
                  <td>
                    <Link className="link" href={`/roasters/${r.id}`}>
                      {r.name}
                    </Link>
                  </td>
                  <td>{r.city ?? "–"}</td>
                  <td>{r.country ?? "–"}</td>
                  <td>
                    {r.website ? (
                      <a className="link" href={r.website.startsWith("http") ? r.website : `https://${r.website}`} target="_blank" rel="noreferrer">
                        <Badge tone="good">Website</Badge>
                      </a>
                    ) : (
                      <Badge tone="warn">fehlend</Badge>
                    )}
                  </td>
                </tr>
              ))}
              {!filtered.length ? (
                <tr>
                  <td colSpan={5} className="muted" style={{ padding: 16 }}>
                    Keine Treffer.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
