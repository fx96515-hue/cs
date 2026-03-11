"use client";

import React from "react";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

const defaultIcon = (
  <svg
    width="48"
    height="48"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ opacity: 0.3 }}
  >
    <rect x="2" y="7" width="20" height="14" rx="2" />
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
  </svg>
);

export default function EmptyState({
  icon = defaultIcon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="emptyState">
      <div className="emptyStateIcon">{icon}</div>
      <div className="emptyStateTitle">{title}</div>
      {description && <div className="emptyStateText">{description}</div>}
      {action}
    </div>
  );
}
