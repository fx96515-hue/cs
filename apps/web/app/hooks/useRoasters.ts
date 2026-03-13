import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, isDemoMode } from "../../lib/api";
import { Roaster, RoasterFilters, Paged } from "../types";

function toPagedRoasters(
  items: Roaster[],
  filters: Partial<RoasterFilters> & { limit?: number; page?: number },
): Paged<Roaster> {
  return {
    items,
    total: items.length,
    page: Number(filters.page ?? 1),
    limit: Number(filters.limit ?? 25),
  };
}

// Fetch Roasters with filters
export function useRoasters(filters: Partial<RoasterFilters> & { limit?: number; page?: number }) {
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
      if (isDemoMode()) return toPagedRoasters([], filters);
      const qs = params.toString();
      const response = await apiFetch<Roaster[] | Paged<Roaster>>(
        `/roasters${qs ? `?${qs}` : ""}`,
      );
      if (Array.isArray(response)) {
        return toPagedRoasters(response, filters);
      }
      return response;
    },
    staleTime: 5 * 60 * 1000,
    placeholderData: { items: [], total: 0, page: 1, limit: 25 },
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
