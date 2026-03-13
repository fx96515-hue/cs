/**
 * services/shipments.service.ts
 * Service für Sendungen / Logistik.
 */
import { apiFetch } from "../../lib/api";

export interface Shipment {
  id: number;
  lot_id?: number;
  lot_reference?: string;
  cooperative_name?: string;
  roaster_id?: number;
  roaster_name?: string;
  origin_port?: string;
  destination_port?: string;
  departure_date?: string;
  estimated_arrival?: string;
  actual_arrival?: string;
  weight_kg?: number;
  container_id?: string;
  status?: "in_transit" | "arrived" | "customs" | "delivered" | "delayed";
  tracking_url?: string;
  notes?: string;
  created_at?: string;
}

export const ShipmentsService = {
  async list(params: { status?: string; roaster_id?: number } = {}): Promise<Shipment[]> {
    const qs = new URLSearchParams();
    if (params.status) qs.set("status", params.status);
    if (params.roaster_id) qs.set("roaster_id", String(params.roaster_id));
    const query = qs.toString();
    const result = await apiFetch<Shipment[]>(`/shipments${query ? `?${query}` : ""}`);
    return Array.isArray(result) ? result : [];
  },

  async getById(id: number): Promise<Shipment> {
    return apiFetch<Shipment>(`/shipments/${id}`);
  },

  async create(data: Partial<Shipment>): Promise<Shipment> {
    return apiFetch<Shipment>("/shipments", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async update(id: number, data: Partial<Shipment>): Promise<Shipment> {
    return apiFetch<Shipment>(`/shipments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};
