
import { useSearchParams } from "react-router-dom";
import type { Filters } from "@/api/types";

export function useFilters(): [Filters, (patch: Partial<Filters>) => void] {
const [sp, setSp] = useSearchParams();
const filters: Filters = {
    date_min: sp.get("date_min") ?? undefined, date_max: sp.get("date_max") ?? undefined,
    region: sp.get("region") ?? undefined, transporteur: sp.get("transporteur") ?? undefined,
};
const update = (patch: Partial<Filters>) => {
    const next = new URLSearchParams(sp);
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setSp(next, { replace: true });
};
return [filters, update];
}