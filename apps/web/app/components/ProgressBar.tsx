"use client";

import React from "react";

interface ProgressBarProps {
  value: number;
  showLabel?: boolean;
  size?: "sm" | "md";
}

export default function ProgressBar({ value, showLabel = true, size = "md" }: ProgressBarProps) {
  const clampedValue = Math.max(0, Math.min(100, value));
  const height = size === "sm" ? 4 : 6;

  return (
    <div>
      {showLabel && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "12px",
            marginBottom: "6px",
            color: "var(--muted)",
          }}
        >
          <span>Fortschritt</span>
          <span style={{ fontWeight: 600, color: "var(--text)" }}>{Math.round(clampedValue)}%</span>
        </div>
      )}
      <div className="progressBar" style={{ height }}>
        <div
          className="progressBarFill"
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
}
