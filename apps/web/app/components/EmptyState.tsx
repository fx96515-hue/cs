"use client";

import React from "react";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  text?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, text, action }: EmptyStateProps) {
  const defaultIcon = (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect width="18" height="18" x="3" y="3" rx="2" />
      <path d="M3 9h18" />
      <path d="M9 21V9" />
    </svg>
  );

  const copy = description ?? text;

  return (
    <div className="emptyState">
      <div className="emptyStateIcon">{icon ?? defaultIcon}</div>
      <div>
        <div className="emptyStateTitle">{title}</div>
        {copy && <p className="emptyStateText">{copy}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

export default EmptyState;

export function DemoEmptyState({ entity = "Daten" }: { entity?: string }) {
  return (
    <EmptyState
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 8v4" />
          <path d="M12 16h.01" />
        </svg>
      }
      title={`Keine ${entity} im Demo-Modus`}
      description="Im Demo-Modus werden keine echten Daten geladen. Starte das Backend und melde dich mit echten Zugangsdaten an."
    />
  );
}

export function SkeletonText({ width = "wide" }: { width?: "wide" | "mid" | "short" }) {
  return <div className={`skeleton skeletonText ${width}`} />;
}

export function SkeletonRows(props: { count?: number; rows?: number; cols?: number }) {
  const rowCount = props.rows ?? props.count ?? 5;

  return (
    <>
      {Array.from({ length: rowCount }).map((_, i) => (
        <div key={i} className="skeletonRow">
          <div className="skeleton skeletonText short" style={{ width: 120 }} />
          <div className="skeleton skeletonText mid" style={{ flex: 1 }} />
          <div className="skeleton skeletonText short" style={{ width: 80 }} />
          <div className="skeleton skeletonText short" style={{ width: 60 }} />
        </div>
      ))}
    </>
  );
}

export function SkeletonKpiGrid({ count = 4 }: { count?: number }) {
  return (
    <div className="kpiGrid">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="kpiCard">
          <div className="skeleton skeletonText short" style={{ width: 90 }} />
          <div className="skeleton" style={{ height: 32, width: 80, borderRadius: 4 }} />
          <div className="skeleton skeletonText mid" style={{ width: 110 }} />
        </div>
      ))}
    </div>
  );
}
