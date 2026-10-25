import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { Bottleneck, Commande, Entrepot, EtlRun, Expedition, Filters, Kpi, Page, TimePoint, Transporteur } from "./types";

const clean = (f: Filters) => Object.fromEntries(Object.entries(f).filter(([, v]) => v));
    export const useSummary = (f: Filters) =>
    useQuery({ queryKey: ["summary", f], queryFn: async () => (await api.get<Kpi>("/kpis/summary/", {
        params: clean(f) })).data });
    export const useTimeseries = (f: Filters, granularity = "week") =>
    useQuery({ queryKey: ["ts", f, granularity],
            queryFn: async () => (await api.get<TimePoint[]>("/kpis/timeseries/", { params: {
                ...clean(f), granularity } })).data });
                
export const useBottlenecks = (f: Filters, by: string, limit = 10, minVolume = 100) =>
useQuery({ queryKey: ["bn", f, by, limit, minVolume],
            queryFn: async () => (await api.get<Bottleneck[]>("/kpis/bottlenecks/", { params: {
                ...clean(f), by, limit, min_volume: minVolume } })).data });

export const useTransporteurs = () => useQuery({
  queryKey: ["transporteurs"],
  queryFn: async () => (await api.get<Transporteur[]>("/transporteurs/")).data,
});
export const useEntrepots = () => useQuery({
  queryKey: ["entrepots"],
  queryFn: async () => (await api.get<Entrepot[]>("/entrepots/")).data,
});

export function useCommandes(page: number, filters: Filters) {
  return useQuery({
    queryKey: ["commandes", page, filters],
    queryFn: async () => (await api.get<Page<Commande>>("/commandes/", { params: { ...clean(filters), page, ordering: "-date_commande" } })).data,
  });
}
export function useExpeditions(page: number, filters: Filters) {
  return useQuery({
    queryKey: ["expeditions", page, filters],
    queryFn: async () => (await api.get<Page<Expedition>>("/expeditions/", { params: { ...clean(filters), page, ordering: "-commande__date_commande" } })).data,
  });
}
export function useEtlRuns(page: number) {
  return useQuery({
    queryKey: ["etl-runs", page],
    queryFn: async () => (await api.get<Page<EtlRun>>("/etl/runs/", { params: { page, ordering: "-started_at" } })).data,
  });
}
