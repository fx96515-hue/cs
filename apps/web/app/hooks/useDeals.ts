import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/api";
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

// Fetch Deals with filters (using lots as base for now)
export function useDeals(filters?: DealFilters & { limit?: number; page?: number }) {
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
      // Using lots endpoint as deals base
      const response = await apiFetch<Deal[] | Paged<Deal>>(`/lots?${params.toString()}`);
      // Backend may return flat list, but we need Paged format
      if (Array.isArray(response)) {
        return { items: response, total: response.length } as Paged<Deal>;
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
      const data = await apiFetch<Deal>(`/lots/${id}`);
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
      profile?: string;
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

// Create Deal (using lot endpoint)
export function useCreateDeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CreateDealRequest) => {
      return await apiFetch<Deal>("/lots", {
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
      return await apiFetch<Deal>(`/lots/${id}`, {
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
