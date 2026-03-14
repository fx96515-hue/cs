"use client";

import React from "react";

interface PaginationProps {
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  pageSizeOptions?: number[];
}

export function Pagination({
  total,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [25, 50, 100],
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  // Seitenzahlen berechnen (max 7 Buttons)
  const getPages = () => {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
    if (page <= 4) return [1, 2, 3, 4, 5, "...", totalPages];
    if (page >= totalPages - 3) return [1, "...", totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
    return [1, "...", page - 1, page, page + 1, "...", totalPages];
  };

  return (
    <div className="pagination">
      <span className="paginationInfo">
        {total === 0 ? "Keine Einträge" : `${from}–${to} von ${total} Einträgen`}
      </span>

      <div className="paginationControls">
        <button
          className="paginationBtn"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Vorherige Seite"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>

        {getPages().map((p, i) =>
          p === "..." ? (
            <span key={`sep-${i}`} style={{ padding: "0 4px", color: "var(--color-text-muted)", fontSize: "var(--font-size-sm)" }}>…</span>
          ) : (
            <button
              key={p}
              className={`paginationBtn ${p === page ? "active" : ""}`}
              onClick={() => onPageChange(p as number)}
              aria-label={`Seite ${p}`}
              aria-current={p === page ? "page" : undefined}
            >
              {p}
            </button>
          )
        )}

        <button
          className="paginationBtn"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          aria-label="Nächste Seite"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>

      {onPageSizeChange && (
        <div className="paginationSize">
          <span>Zeilen:</span>
          <select
            className="input"
            style={{ height: 32, width: 70, fontSize: "var(--font-size-sm)", padding: "0 8px" }}
            value={pageSize}
            onChange={(e) => { onPageSizeChange(Number(e.target.value)); onPageChange(1); }}
            aria-label="Einträge pro Seite"
          >
            {pageSizeOptions.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  usePagination Hook                                                  */
/* ------------------------------------------------------------------ */

export function usePagination<T>(items: T[], defaultPageSize = 25) {
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(defaultPageSize);

  React.useEffect(() => { setPage(1); }, [items.length]);

  const paginated = items.slice((page - 1) * pageSize, page * pageSize);

  return {
    page,
    pageSize,
    setPage,
    setPageSize,
    paginated,
    total: items.length,
  };
}
