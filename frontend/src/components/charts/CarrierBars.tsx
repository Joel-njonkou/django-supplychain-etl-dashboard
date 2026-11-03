import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { Bottleneck } from "@/api/types";
import { formater } from "@/lib/format";

interface Props {
  lignes: Bottleneck[];
  actif?: string;
  onChoisir: (nomTransporteur: string) => void;
}

export default function CarrierBars({ lignes, actif, onChoisir }: Props) {
  const donnees = lignes
    .filter((l) => l.transporteur && l.taux_retard != null)
    .map((l) => ({
      transporteur: l.transporteur as string,
      taux: Math.round((l.taux_retard as number) * 1000) / 10,
      libelle: formater(l.taux_retard, "pct"),
    }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={donnees} margin={{ top: 24, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="transporteur" tick={{ fontSize: 11 }} interval={0} />
        <YAxis domain={[0, 100]} unit=" %" tick={{ fontSize: 11 }} width={48} />
        <Tooltip formatter={(valeur) => [`${valeur} %`, "Taux de retard"]} />
        <Bar dataKey="taux" isAnimationActive={false}>
          <LabelList dataKey="libelle" position="top" fontSize={11} />
          {donnees.map((d) => (
            <Cell
              key={d.transporteur}
              fill={d.transporteur === actif ? "#0E9F8E" : "#94a3b8"}
              cursor="pointer"
              onClick={() => onChoisir(d.transporteur)}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}