import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";
import {
  PeruRegion,
  Cooperative,
  CooperativeFilters,
  Paged,
  RegionIntelligence,
} from "../types";

// Fetch Peru Regions
export function usePeruRegions() {
  return useQuery({
    queryKey: ["peru-regions"],
    queryFn: async () => {
      const data = await apiFetch<PeruRegion[]>("/regions/peru");
      return data;
    },
  });
}

// Fetch Peru Region Intelligence
export function usePeruRegionIntelligence(regionName: string) {
  return useQuery({
    queryKey: ["peru-region-intelligence", regionName],
    queryFn: async () => {
      const data = await apiFetch<RegionIntelligence>(
        `/peru/regions/${encodeURIComponent(regionName)}/intelligence`
      );
      return data;
    },
    enabled: !!regionName,
  });
}

// Fetch Cooperatives with filters
export function useCooperatives(filters?: CooperativeFilters & { limit?: number; page?: number }) {
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
    queryKey: ["cooperatives", filters],
    queryFn: async () => {
      const response = await apiFetch<Cooperative[] | Paged<Cooperative>>(
        `/cooperatives?${params.toString()}`
      );
      // Backend returns flat list, but we need Paged format
      // Check if response is already in Paged format
      if (Array.isArray(response)) {
        return { items: response, total: response.length } as Paged<Cooperative>;
      }
      return response;
    },
  });
}

// Fetch single Cooperative
export function useCooperative(id: number) {
  return useQuery({
    queryKey: ["cooperative", id],
    queryFn: async () => {
      const data = await apiFetch<Cooperative>(`/cooperatives/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// Create Cooperative
export function useCreateCooperative() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Cooperative>) => {
      return await apiFetch<Cooperative>("/cooperatives", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cooperatives"] });
    },
  });
}

// Update Cooperative
export function useUpdateCooperative() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Cooperative> }) => {
      return await apiFetch<Cooperative>(`/cooperatives/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cooperatives"] });
      queryClient.invalidateQueries({ queryKey: ["cooperative", variables.id] });
    },
  });
}
