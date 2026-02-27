import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";
import { Shipment, ShipmentFilters, Paged } from "../types";

// Fetch Shipments with filters
export function useShipments(filters?: ShipmentFilters & { limit?: number; page?: number }) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach((v) => params.append(key, String(v)));
        } else {
          params.set(key, String(value));
        }
      }
    });
  }

  return useQuery({
    queryKey: ["shipments", filters],
    queryFn: async () => {
      const response = await apiFetch<Shipment[]>(`/shipments?${params.toString()}`);
      // Backend returns flat list
      if (Array.isArray(response)) {
        return { items: response, total: response.length } as Paged<Shipment>;
      }
      return response as Paged<Shipment>;
    },
  });
}

// Fetch single Shipment
export function useShipment(id: number) {
  return useQuery({
    queryKey: ["shipment", id],
    queryFn: async () => {
      const data = await apiFetch<Shipment>(`/shipments/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// Fetch active shipments (in_transit)
export function useActiveShipments() {
  return useQuery({
    queryKey: ["shipments", "active"],
    queryFn: async () => {
      const response = await apiFetch<Shipment[]>("/shipments/active");
      return response;
    },
  });
}

// Create Shipment
export function useCreateShipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      lot_id?: number | null;
      cooperative_id?: number | null;
      roaster_id?: number | null;
      container_number: string;
      bill_of_lading: string;
      weight_kg: number;
      container_type: string;
      origin_port: string;
      destination_port: string;
      departure_date?: string | null;
      estimated_arrival?: string | null;
      notes?: string | null;
    }) => {
      return await apiFetch<Shipment>("/shipments", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shipments"] });
    },
  });
}

// Update Shipment
export function useUpdateShipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: number;
      data: {
        current_location?: string;
        status?: string;
        actual_arrival?: string;
        delay_hours?: number;
        notes?: string;
      };
    }) => {
      return await apiFetch<Shipment>(`/shipments/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["shipments"] });
      queryClient.invalidateQueries({ queryKey: ["shipment", variables.id] });
    },
  });
}
