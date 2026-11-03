import { useBottlenecks, useTransporteurs } from "@/api/hooks";
import type { Filters } from "@/api/types";

interface Props {
  filtres: Filters;
  onChange: (modifications: Partial<Filters>) => void;
}

const CHAMP = "mt-1 block rounded border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900";

export default function FilterBar({ filtres, onChange }: Props) {
  const transporteurs = useTransporteurs();
  const parRegion = useBottlenecks({}, "region", 100);
  const regions = (parRegion.data ?? [])
    .map((l) => l.region)
    .filter((r): r is string => Boolean(r))
    .sort((a, b) => a.localeCompare(b, "fr"));
  const filtresActifs = Object.keys(filtres).length > 0;

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <label className="text-xs font-medium text-slate-500">
        Du
        <input
          type="date"
          value={filtres.date_min ?? ""}
          min="2015-01-01"
          max="2018-01-31"
          onChange={(e) => onChange({ date_min: e.target.value })}
          className={CHAMP}
        />
      </label>

      <label className="text-xs font-medium text-slate-500">
        Au
        <input
          type="date"
          value={filtres.date_max ?? ""}
          min="2015-01-01"
          max="2018-01-31"
          onChange={(e) => onChange({ date_max: e.target.value })}
          className={CHAMP}
        />
      </label>

      <label className="text-xs font-medium text-slate-500">
        Transporteur
        <select
          value={filtres.transporteur ?? ""}
          onChange={(e) => onChange({ transporteur: e.target.value })}
          className={CHAMP}
        >
          <option value="">Tous</option>
          {transporteurs.data?.map((t) => (
            <option key={t.code} value={t.code}>
              {t.nom}
            </option>
          ))}
        </select>
      </label>

      <label className="text-xs font-medium text-slate-500">
        Région
        <select
          value={filtres.region ?? ""}
          onChange={(e) => onChange({ region: e.target.value })}
          className={CHAMP}
        >
          <option value="">Toutes</option>
          {regions.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </label>

      {filtresActifs && (
        <button
          type="button"
          onClick={() =>
            onChange({ date_min: undefined, date_max: undefined, region: undefined, transporteur: undefined, marche: undefined })
          }
          className="ml-auto text-sm text-slate-500 underline hover:text-slate-900"
        >
          Réinitialiser les filtres
        </button>
      )}
    </div>
  );
}