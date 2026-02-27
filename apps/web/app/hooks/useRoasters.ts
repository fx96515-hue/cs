import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";
import { Roaster, RoasterFilters, Paged } from "../types";

// Fetch Roasters with filters
export function useRoasters(filters?: RoasterFilters & { limit?: number; page?: number }) {
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
    queryKey: ["roasters", filters],
    queryFn: async () => {
      const response = await apiFetch<Roaster[] | Paged<Roaster>>(`/roasters?${params.toString()}`);
      // Backend returns flat list, but we need Paged format
      // Check if response is already in Paged format
      if (Array.isArray(response)) {
        return { items: response, total: response.length } as Paged<Roaster>;
      }
      return response;
    },
  });
}

// Fetch single Roaster
export function useRoaster(id: number) {
  return useQuery({
    queryKey: ["roaster", id],
    queryFn: async () => {
      const data = await apiFetch<Roaster>(`/roasters/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// Create Roaster
export function useCreateRoaster() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Roaster>) => {
      return await apiFetch<Roaster>("/roasters", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roasters"] });
    },
  });
}

// Update Roaster
export function useUpdateRoaster() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Roaster> }) => {
      return await apiFetch<Roaster>(`/roasters/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["roasters"] });
      queryClient.invalidateQueries({ queryKey: ["roaster", variables.id] });
    },
  });
}
