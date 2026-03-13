/**
 * services/alerts.service.ts
 * Service für Betriebsmeldungen und Warnungen.
 */
import { apiFetch } from "../../lib/api";

export interface Alert {
  id: number;
  entity_type?: string;
  entity_id?: number;
  entity_name?: string;
  severity?: "info" | "warning" | "critical";
  message?: string;
  resolved?: boolean;
  created_at?: string;
  resolved_at?: string;
}

export const AlertsService = {
  async list(params: { resolved?: boolean; severity?: string; entity_type?: string } = {}): Promise<Alert[]> {
    const qs = new URLSearchParams();
    if (params.resolved !== undefined) qs.set("resolved", String(params.resolved));
    if (params.severity) qs.set("severity", params.severity);
    if (params.entity_type) qs.set("entity_type", params.entity_type);
    const query = qs.toString();
    const result = await apiFetch<Alert[]>(`/alerts${query ? `?${query}` : ""}`);
    return Array.isArray(result) ? result : [];
  },

  async resolve(id: number): Promise<Alert> {
    return apiFetch<Alert>(`/alerts/${id}/resolve`, { method: "POST" });
  },

  async dismiss(id: number): Promise<void> {
    return apiFetch(`/alerts/${id}`, { method: "DELETE" });
  },
};
