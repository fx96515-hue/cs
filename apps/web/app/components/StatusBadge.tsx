"use client";

import React from "react";

export type ShipmentStatus = "in_transit" | "arrived" | "delivered" | "delayed" | "pending" | "archived";

const statusConfig: Record<string, { label: string; className: string }> = {
  in_transit: { label: "In Transit", className: "badge statusInTransit" },
  arrived: { label: "Angekommen", className: "badge statusArrived" },
  delivered: { label: "Geliefert", className: "badge statusArrived" },
  delayed: { label: "Verspaetet", className: "badge statusDelayed" },
  pending: { label: "Ausstehend", className: "badge statusPending" },
  archived: { label: "Archiviert", className: "badge badgeWarn" },
};

interface StatusBadgeProps {
  status: string;
  isArchived?: boolean;
}

export default function StatusBadge({ status, isArchived }: StatusBadgeProps) {
  if (isArchived) {
    return <span className="badge badgeWarn">Archiviert</span>;
  }

  const config = statusConfig[status] || { label: status.replace(/_/g, " "), className: "badge" };

  return <span className={config.className}>{config.label}</span>;
}
