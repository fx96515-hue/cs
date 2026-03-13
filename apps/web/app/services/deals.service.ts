/**
 * services/deals.service.ts
 * Service für Deals & Margenkalkulation.
 */
import { apiFetch } from "../../lib/api";

export interface Deal {
  id: number;
  roaster_id?: number;
  roaster_name?: string;
  cooperative_id?: number;
  cooperative_name?: string;
  lot_id?: number;
  quantity_kg?: number;
  price_per_kg_eur?: number;
  status?: "draft" | "negotiating" | "confirmed" | "closed" | "cancelled";
  deal_date?: string;
  notes?: string;
  margin_pct?: number;
  cost_per_kg_roasted?: number;
  created_at?: string;
  updated_at?: string;
}

export const DealsService = {
  async list(params: { status?: string; roaster_id?: number; cooperative_id?: number } = {}): Promise<Deal[]> {
    const qs = new URLSearchParams();
    if (params.status) qs.set("status", params.status);
    if (params.roaster_id) qs.set("roaster_id", String(params.roaster_id));
    if (params.cooperative_id) qs.set("cooperative_id", String(params.cooperative_id));
    const query = qs.toString();
    const result = await apiFetch<Deal[]>(`/deals${query ? `?${query}` : ""}`);
    return Array.isArray(result) ? result : [];
  },

  async getById(id: number): Promise<Deal> {
    return apiFetch<Deal>(`/deals/${id}`);
  },

  async create(data: Partial<Deal>): Promise<Deal> {
    return apiFetch<Deal>("/deals", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async update(id: number, data: Partial<Deal>): Promise<Deal> {
    return apiFetch<Deal>(`/deals/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};
