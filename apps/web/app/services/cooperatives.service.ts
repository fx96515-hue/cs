/**
 * services/cooperatives.service.ts
 * Service für alle Kooperativen-Operationen.
 */
import { apiFetch } from "../../lib/api";

export interface Cooperative {
  id: number;
  name: string;
  region?: string;
  country?: string;
  country_code?: string;
  altitude_min?: number;
  altitude_max?: number;
  certifications?: string[];
  website?: string;
  contact_email?: string;
  founded_year?: number;
  members_count?: number;
  notes?: string;
  latitude?: number;
  longitude?: number;
  data_quality_score?: number;
  data_quality_flags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface CooperativesListParams {
  search?: string;
  country?: string;
  region?: string;
  page?: number;
  page_size?: number;
}

export const CooperativesService = {
  async list(params: CooperativesListParams = {}): Promise<Cooperative[]> {
    const qs = new URLSearchParams();
    if (params.search) qs.set("search", params.search);
    if (params.country) qs.set("country", params.country);
    if (params.region) qs.set("region", params.region);
    if (params.page) qs.set("page", String(params.page));
    if (params.page_size) qs.set("page_size", String(params.page_size));
    const query = qs.toString();
    const result = await apiFetch<Cooperative[]>(`/cooperatives${query ? `?${query}` : ""}`);
    return Array.isArray(result) ? result : [];
  },

  async getById(id: number): Promise<Cooperative> {
    return apiFetch<Cooperative>(`/cooperatives/${id}`);
  },

  async create(data: Partial<Cooperative>): Promise<Cooperative> {
    return apiFetch<Cooperative>("/cooperatives", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async update(id: number, data: Partial<Cooperative>): Promise<Cooperative> {
    return apiFetch<Cooperative>(`/cooperatives/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async enrich(id: number): Promise<{ status: string; message: string }> {
    return apiFetch(`/cooperatives/${id}/enrich`, { method: "POST" });
  },
};
