
import type { Bottleneck } from "@/api/types";

const color = (t: number | null) => (t == null ? "#f1f5f9" : `hsl(${Math.round(120 - 120 * t)}, 70%, ${90 - 35 * t}%)`);   // vert -> rouge
export function BottleneckHeatmap({ rows, onPick }: { rows: Bottleneck[]; onPick: (region: string,
    transporteur: string) => void }) {
const regions = [...new Set(rows.map((r) => r.region!))];
const carriers = [...new Set(rows.map((r) => r.transporteur!))];
  const cell = (rg: string, tr: string) => rows.find((r) => r.region === rg && r.transporteur ===
tr); return (
    <div className="overflow-x-auto">
      <table className="text-xs">
        <thead><tr><th />{carriers.map((c) => <th key={c} className="px-2 py-1 font-medium text-
            slate-500">{c}</th>)}</tr></thead>
        <tbody>
          {regions.map((rg) => (
            <tr key={rg}>
              <th className="pr-2 text-right font-normal text-slate-600">{rg}</th>
              {carriers.map((tr) => {
                const c = cell(rg, tr);
                return (
                  <td key={tr} className="cursor-pointer border border-white px-2 py-1 text-center"
                      style={{ background: color(c?.taux_retard ?? null) }}
                      title={c ? `${c.retards} retards / ${c.volume} expéditions` : "Trop peu de données"}
                      onClick={() => c && onPick(rg, tr)}>
                    {c?.taux_retard == null ? "·" : `${Math.round(c.taux_retard * 100)} %`}
                  </td>);
})} </tr>))}
        </tbody>
      </table>
</div> );
}