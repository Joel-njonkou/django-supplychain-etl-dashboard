import type { Bottleneck } from "@/api/types";
import { formater } from "@/lib/format";

interface Props {
  lignes: Bottleneck[];
  regionActive?: string;
  transporteurActif?: string;
  onChoisir: (region: string, nomTransporteur: string) => void;
}

function couleur(taux: number | null | undefined): string {
  if (taux == null) return "#f1f5f9";
  return `hsl(${Math.round(120 - 120 * taux)}, 70%, ${Math.round(90 - 35 * taux)}%)`;
}

export default function BottleneckHeatmap({ lignes, regionActive, transporteurActif, onChoisir }: Props) {
  const regions = [...new Set(lignes.map((l) => l.region ?? ""))].filter(Boolean).sort();
  const transporteurs = [...new Set(lignes.map((l) => l.transporteur ?? ""))].filter(Boolean).sort();
  const cellule = (region: string, transporteur: string) =>
    lignes.find((l) => l.region === region && l.transporteur === transporteur);

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            <th />
            {transporteurs.map((t) => (
              <th key={t} scope="col" className="px-2 py-1 font-medium text-slate-500">
                {t}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {regions.map((region) => (
            <tr key={region}>
              <th scope="row" className="whitespace-nowrap pr-2 text-right font-normal text-slate-600">
                {region}
              </th>
              {transporteurs.map((t) => {
                const c = cellule(region, t);
                const selectionnee = region === regionActive && t === transporteurActif;
                return (
                  <td
                    key={t}
                    className={`border border-white px-2 py-1 text-center text-slate-900 ${c ? "cursor-pointer" : ""} ${selectionnee ? "outline-2 outline-slate-900" : ""}`}
                    style={{ background: couleur(c?.taux_retard) }}
                    title={c ? `${c.retards} retards sur ${c.volume} expéditions` : "Moins de 100 expéditions : non affiché"}
                    onClick={() => c && onChoisir(region, t)}
                  >
                    {c?.taux_retard == null ? "·" : formater(c.taux_retard, "pct")}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}