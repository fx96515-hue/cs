"use client";

import React from "react";

/* ------------------------------------------------------------------ */
/*  ErrorPanel – einheitliche Fehlermeldung mit optionalem Retry       */
/* ------------------------------------------------------------------ */

interface ErrorPanelProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorPanel({ message, onRetry }: ErrorPanelProps) {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: "var(--space-4)",
      padding: "var(--space-12) var(--space-6)",
      textAlign: "center",
    }}>
      <div style={{
        width: 48,
        height: 48,
        borderRadius: "var(--radius-xl)",
        background: "var(--color-danger-subtle)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--color-danger)",
      }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <div>
        <div style={{ fontWeight: "var(--font-weight-semibold)", color: "var(--color-text)", marginBottom: "var(--space-1)" }}>
          Fehler beim Laden
        </div>
        <div style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)", maxWidth: 360 }}>
          {message}
        </div>
      </div>
      {onRetry && (
        <button className="btn btnSecondary btnSm" onClick={onRetry} type="button">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 6 }}>
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Erneut versuchen
        </button>
      )}
    </div>
  );
}
