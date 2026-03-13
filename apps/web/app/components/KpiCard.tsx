import React from "react";

interface KpiCardProps {
  label: string;
  value: React.ReactNode;
  hint?: string;
  trend?: {
    value: string;
    direction: "up" | "down" | "neutral";
  };
}

export default function KpiCard({ label, value, hint, trend }: KpiCardProps) {
  return (
    <div className="kpiCard">
      <div className="cardLabel">{label}</div>
      <div className="cardValue">{value}</div>
      {trend && (
        <div className={`cardTrend ${trend.direction}`}>
          {trend.direction === "up" && (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 2L10 6H7V10H5V6H2L6 2Z" fill="currentColor" />
            </svg>
          )}
          {trend.direction === "down" && (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 10L2 6H5V2H7V6H10L6 10Z" fill="currentColor" />
            </svg>
          )}
          <span>{trend.value}</span>
        </div>
      )}
      {hint && <div className="cardHint">{hint}</div>}
    </div>
  );
}
