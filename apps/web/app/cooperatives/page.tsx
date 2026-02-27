"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import Badge from "../components/Badge";

type Coop = {
  id: number;
  name: string;
  region?: string | null;
  country?: string | null;
  website?: string | null;
  sca_score?: number | null;
};

type CoopList = { items: Coop[]; total: number };

export default function CooperativesPage() {
  const [data, setData] = useState<CoopList | null>(null);
  const [q, setQ] = useState("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch<Coop[] | CoopList>(`/cooperatives?limit=200`);
        // Backend returns flat list, but we need { items, total } format
        if (Array.isArray(res)) {
          setData({ items: res, total: res.length });
        } else {
          setData(res);
        }
      } catch (e: any) {
        setErr(e?.message ?? String(e));
      }
    })();
  }, []);

  const rows = useMemo(() => {
    const items = data?.items ?? [];
    const qq = q.trim().toLowerCase();
    if (!qq) return items;
    return items.filter((c) =>
      [c.name, c.region ?? "", c.country ?? "", c.website ?? ""].join(" ").toLowerCase().includes(qq),
    );
  }, [data, q]);

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="h1">Kooperativen</div>
          <div className="muted">Alles an einem Ort – Suche, Bewertung, Website, Enrichment.</div>
        </div>
        <div className="row gap">
          <input
            className="input"
            placeholder="Suchen (Name, Region, Website)…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <Link className="btn" href="/ops">
            Enrichment starten
          </Link>
        </div>
      </div>

      {err ? <div className="error">{err}</div> : null}

      <div className="panel">
        <div className="panelTitle">
          Treffer: {rows.length} {data ? <span className="muted">(gesamt {data.total})</span> : null}
        </div>

        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Region</th>
                <th>Land</th>
                <th>Website</th>
                <th>SCA</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link className="link" href={`/cooperatives/${c.id}`}>
                      {c.name}
                    </Link>
                  </td>
                  <td className="muted">{c.region ?? "–"}</td>
                  <td className="muted">{c.country ?? "–"}</td>
                  <td>
                    {c.website ? (
                      <a className="link" href={(c.website.startsWith("http") ? c.website : `https://${c.website}`)} target="_blank" rel="noreferrer">
                        {c.website}
                      </a>
                    ) : (
                      <Badge tone="warn">fehlend</Badge>
                    )}
                  </td>
                  <td>{c.sca_score ? <Badge tone="good">{c.sca_score}</Badge> : <Badge>–</Badge>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
