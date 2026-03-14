/**
 * services/lots.service.ts
 * Service für Kaffee-Partien (Lots).
 */
import { apiFetch } from "../../lib/api";

export interface Lot {
  id: number;
  cooperative_id?: number;
  cooperative_name?: string;
  crop_year?: number;
  process?: string;
  variety?: string;
  screen_size?: string;
  moisture_pct?: number;
  cupping_score?: number;
  available_kg?: number;
  fob_price_usd?: number;
  status?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LotMarginInput {
  lot_id: number;
  freight_usd_per_kg?: number;
  roast_loss_pct?: number;
  overhead_usd_per_kg?: number;
  target_sell_price_eur?: number;
}

export interface LotMarginResult {
  cif_price_usd?: number;
  cost_per_kg_roasted?: number;
  margin_pct?: number;
  margin_eur_per_kg?: number;
  recommendation?: string;
}

export const LotsService = {
  async list(params: { cooperative_id?: number; status?: string; search?: string } = {}): Promise<Lot[]> {
    const qs = new URLSearchParams();
    if (params.cooperative_id) qs.set("cooperative_id", String(params.cooperative_id));
    if (params.status) qs.set("status", params.status);
    if (params.search) qs.set("search", params.search);
    const query = qs.toString();
    const result = await apiFetch<Lot[]>(`/lots${query ? `?${query}` : ""}`);
    return Array.isArray(result) ? result : [];
  },

  async getById(id: number): Promise<Lot> {
    return apiFetch<Lot>(`/lots/${id}`);
  },

  async create(data: Partial<Lot>): Promise<Lot> {
    return apiFetch<Lot>("/lots", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async update(id: number, data: Partial<Lot>): Promise<Lot> {
    return apiFetch<Lot>(`/lots/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async calculateMargin(input: LotMarginInput): Promise<LotMarginResult> {
    return apiFetch<LotMarginResult>(`/lots/${input.lot_id}/margin`, {
      method: "POST",
      body: JSON.stringify(input),
    });
  },
};
