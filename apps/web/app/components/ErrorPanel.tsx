"use client";

import type { CSSProperties } from "react";

interface ErrorPanelProps {
  message: string;
  onRetry?: () => void;
  style?: CSSProperties;
  compact?: boolean;
}

export function ErrorPanel({ message, onRetry, style, compact }: ErrorPanelProps) {
  if (compact) {
    return (
      <div className="alert bad" style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", ...style }}>
        <span className="alertText">{message}</span>
        {onRetry && (
          <button type="button" className="btn btnGhost btnSm" onClick={onRetry}>
            Wiederholen
          </button>
        )}
      </div>
    );
  }
  return (
    <div className="alert bad" style={{ flexDirection: "column", alignItems: "flex-start", ...style }}>
      <span className="alertText">{message}</span>
      {onRetry && (
        <button type="button" className="btn btnGhost btnSm" onClick={onRetry} style={{ marginTop: "var(--space-2)" }}>
          Wiederholen
        </button>
      )}
    </div>
  );
}

export default ErrorPanel;
