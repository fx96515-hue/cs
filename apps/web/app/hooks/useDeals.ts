import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, isDemoMode } from "../../lib/api";
import { 
  DealFilters, 
  MarginCalcRequest, 
  MarginCalcResult, 
  Paged, 
  Deal, 
  MarginRun,
  CreateDealRequest,
  UpdateDealRequest
} from "../types";

function toPagedDeals(
  items: Deal[],
  filters: DealFilters & { limit?: number; page?: number },
): Paged<Deal> {
  return {
    items,
    total: items.length,
    page: Number(filters.page ?? 1),
    limit: Number(filters.limit ?? 25),
  };
}

// Fetch Deals with filters
export function useDeals(filters: DealFilters & { limit?: number; page?: number }) {
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
    queryKey: ["deals", filters],
    queryFn: async () => {
      if (isDemoMode()) return toPagedDeals([], filters);
      const qs = params.toString();
      const response = await apiFetch<Deal[] | Paged<Deal>>(`/deals${qs ? `?${qs}` : ""}`);
      // Backend may return flat list, but we need Paged format
      if (Array.isArray(response)) {
        return toPagedDeals(response, filters);
      }
      return response;
    },
  });
}

// Fetch single Deal
export function useDeal(id: number) {
  return useQuery({
    queryKey: ["deal", id],
    queryFn: async () => {
      const data = await apiFetch<Deal>(`/deals/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// Calculate Margin
export function useCalculateMargin() {
  return useMutation({
    mutationFn: async (data: MarginCalcRequest) => {
      return await apiFetch<MarginCalcResult>("/margins/calc", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
  });
}

// Save Margin Run for Lot
export function useSaveMarginRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      lotId,
      data,
      profile = "conservative",
    }: {
      lotId: number;
      data: MarginCalcRequest;
      profile: string;
    }) => {
      return await apiFetch<MarginRun>(`/margins/lots/${lotId}/runs?profile=${profile}`, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["margin-runs", variables.lotId] });
    },
  });
}

// Get Margin Runs for Lot
export function useMarginRuns(lotId: number) {
  return useQuery({
    queryKey: ["margin-runs", lotId],
    queryFn: async () => {
      const data = await apiFetch<MarginRun[]>(`/margins/lots/${lotId}/runs`);
      return data;
    },
    enabled: !!lotId,
  });
}

// Create Deal
export function useCreateDeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CreateDealRequest) => {
      return await apiFetch<Deal>("/deals", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deals"] });
    },
  });
}

// Update Deal
export function useUpdateDeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: UpdateDealRequest }) => {
      return await apiFetch<Deal>(`/deals/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["deals"] });
      queryClient.invalidateQueries({ queryKey: ["deal", variables.id] });
    },
  });
}
