import { useState } from "react";

import type { Bottleneck } from "@/api/types";
import { type Format, formater } from "@/lib/format";

type Cle = "region" | "transporteur" | "volume" | "retards" | "taux_retard" | "retard_moyen_jours" | "cout_moyen";

const COLONNES: { cle: Cle; titre: string; format?: Format }[] = [
  { cle: "region", titre: "Région" },
  { cle: "transporteur", titre: "Transporteur" },
  { cle: "volume", titre: "Volume", format: "entier" },
  { cle: "retards", titre: "Retards", format: "entier" },
  { cle: "taux_retard", titre: "Taux de retard", format: "pct" },
  { cle: "retard_moyen_jours", titre: "Retard moyen", format: "jours" },
  { cle: "cout_moyen", titre: "Coût moyen (estimé)", format: "euros" },
];

function comparer(a: string | number | null | undefined, b: string | number | null | undefined): number {
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), "fr");
}

export default function BottleneckTable({ lignes }: { lignes: Bottleneck[] }) {
  const [tri, setTri] = useState<{ cle: Cle; croissant: boolean }>({ cle: "retards", croissant: false });

  const triees = [...lignes].sort((a, b) => {
    const ordre = comparer(a[tri.cle], b[tri.cle]);
    return tri.croissant ? ordre : -ordre;
  });

  function trierPar(cle: Cle) {
    setTri((actuel) => ({ cle, croissant: actuel.cle === cle ? !actuel.croissant : false }));
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
            {COLONNES.map((col) => (
              <th
                key={col.cle}
                scope="col"
                aria-sort={tri.cle === col.cle ? (tri.croissant ? "ascending" : "descending") : "none"}
                className="px-2 py-2 font-medium"
              >
                <button type="button" onClick={() => trierPar(col.cle)} className="hover:text-slate-900">
                  {col.titre}
                  {tri.cle === col.cle ? (tri.croissant ? " ▲" : " ▼") : ""}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {triees.map((l) => (
            <tr key={`${l.region}-${l.transporteur}`} className="border-b border-slate-100">
              {COLONNES.map((col) => (
                <td key={col.cle} className={`px-2 py-1.5 ${col.format ? "text-right tabular-nums" : ""}`}>
                  {col.format ? formater(l[col.cle] as number | null, col.format) : l[col.cle]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}