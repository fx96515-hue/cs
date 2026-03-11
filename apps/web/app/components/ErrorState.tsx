"use client";

import React from "react";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({
  title = "Fehler beim Laden",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="errorState">
      <div className="errorStateTitle">{title}</div>
      <div className="errorStateText">{message}</div>
      {onRetry && (
        <button
          className="btn"
          onClick={onRetry}
          style={{ marginTop: 16 }}
        >
          Erneut versuchen
        </button>
      )}
    </div>
  );
}
