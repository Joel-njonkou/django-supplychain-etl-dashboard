import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/client";
import type {
  Anomaly,
  Bottleneck,
  Expedition,
  Explanation,
  Filters,
  Kpi,
  Page,
  TimePoint,
  Transporteur,
} from "@/api/types";

export type Granularite = "day" | "week" | "month";

export interface ReponseExplication {
  source: "llm" | "template";
  explanation: Explanation;
  evidence?: Record<string, unknown>;
}

function sansVides(filtres: Filters): Record<string, string> {
  return Object.fromEntries(
    Object.entries(filtres).filter(([, valeur]) => valeur !== undefined && valeur !== ""),
  ) as Record<string, string>;
}

export function useSummary(filtres: Filters) {
  return useQuery({
    queryKey: ["summary", filtres],
    queryFn: async () => {
      const reponse = await api.get<Kpi>("/kpis/summary/", { params: sansVides(filtres) });
      return reponse.data;
    },
  });
}

export function useTimeseries(filtres: Filters, granularite: Granularite = "week") {
  return useQuery({
    queryKey: ["timeseries", filtres, granularite],
    queryFn: async () => {
      const reponse = await api.get<TimePoint[]>("/kpis/timeseries/", {
        params: { ...sansVides(filtres), granularity: granularite },
      });
      return reponse.data;
    },
  });
}

export function useBottlenecks(filtres: Filters, by: string, limit = 10) {
  return useQuery({
    queryKey: ["bottlenecks", filtres, by, limit],
    queryFn: async () => {
      const reponse = await api.get<Bottleneck[]>("/kpis/bottlenecks/", {
        params: { ...sansVides(filtres), by, limit },
      });
      return reponse.data;
    },
  });
}

export function useAnomalies(granularite: Granularite = "week") {
  return useQuery({
    queryKey: ["anomalies", granularite],
    queryFn: async () => {
      const reponse = await api.get<Page<Anomaly>>("/anomalies/", {
        params: { granularity: granularite },
      });
      return reponse.data.results;
    },
  });
}

export function useExplain() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, forcer = false }: { id: number; forcer?: boolean }) => {
      const reponse = await api.post<ReponseExplication>(`/anomalies/${id}/explain/`, null, {
        params: forcer ? { refresh: "true" } : {},
      });
      return reponse.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["anomalies"] }),
  });
}

export function useTransporteurs() {
  return useQuery({
    queryKey: ["transporteurs"],
    queryFn: async () => {
      const reponse = await api.get<Transporteur[]>("/transporteurs/");
      return reponse.data;
    },
    staleTime: Infinity,
  });
}

export function useExpeditions(filtres: Filters, page: number, taille: number, tri: string) {
  return useQuery({
    queryKey: ["expeditions", filtres, page, taille, tri],
    queryFn: async () => {
      const reponse = await api.get<Page<Expedition>>("/expeditions/", {
        params: { ...sansVides(filtres), page, page_size: taille, ordering: tri },
      });
      return reponse.data;
    },
    placeholderData: keepPreviousData,
  });
}