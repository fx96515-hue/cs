import React from "react";

export default function KpiCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
}) {
  return (
    <div className="panel card">
      <div className="cardLabel">{label}</div>
      <div className="cardValue">{value}</div>
      {hint ? <div className="cardHint">{hint}</div> : null}
    </div>
  );
}
