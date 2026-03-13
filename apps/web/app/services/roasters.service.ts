/**
 * services/roasters.service.ts
 * Service für alle Rösterei-Operationen.
 */
import { apiFetch } from "../../lib/api";

export interface Roaster {
  id: number;
  name: string;
  city?: string;
  country?: string;
  contact_email?: string;
  website?: string;
  annual_kg?: number;
  specialty_focus?: boolean;
  notes?: string;
  archived?: boolean;
  created_at?: string;
  updated_at?: string;
  data_quality_score?: number;
  data_quality_flags?: string[];
}

export interface RoastersListParams {
  search?: string;
  country?: string;
  archived?: boolean;
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export const RoastersService = {
  /**
   * Alle Röstereien abrufen (paginiert).
   */
  async list(params: RoastersListParams = {}): Promise<Roaster[]> {
    const qs = new URLSearchParams();
    if (params.search) qs.set("search", params.search);
    if (params.country) qs.set("country", params.country);
    if (params.archived !== undefined) qs.set("archived", String(params.archived));
    if (params.page) qs.set("page", String(params.page));
    if (params.page_size) qs.set("page_size", String(params.page_size));
    const query = qs.toString();
    const result = await apiFetch<Roaster[] | PaginatedResponse<Roaster>>(
      `/roasters${query ? `?${query}` : ""}`
    );
    return Array.isArray(result) ? result : (result as PaginatedResponse<Roaster>).items ?? [];
  },

  /**
   * Einzelne Rösterei abrufen.
   */
  async getById(id: number): Promise<Roaster> {
    return apiFetch<Roaster>(`/roasters/${id}`);
  },

  /**
   * Neue Rösterei anlegen.
   */
  async create(data: Partial<Roaster>): Promise<Roaster> {
    return apiFetch<Roaster>("/roasters", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Rösterei aktualisieren.
   */
  async update(id: number, data: Partial<Roaster>): Promise<Roaster> {
    return apiFetch<Roaster>(`/roasters/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Rösterei archivieren (soft delete).
   */
  async archive(id: number): Promise<void> {
    return apiFetch(`/roasters/${id}`, { method: "DELETE" });
  },

  /**
   * Rösterei wiederherstellen.
   */
  async restore(id: number): Promise<Roaster> {
    return apiFetch<Roaster>(`/roasters/${id}/restore`, { method: "POST" });
  },
};
