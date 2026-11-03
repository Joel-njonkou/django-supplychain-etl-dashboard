import { CartesianGrid, Line, LineChart, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { Anomaly, TimePoint } from "@/api/types";

interface Props {
  points: TimePoint[];
  anomalies?: Anomaly[];
}

const enPourcent = (taux: number | null) => (taux == null ? null : Math.round(taux * 1000) / 10);

export default function TimeseriesChart({ points, anomalies = [] }: Props) {
  const lignes = points.map((p) => ({
    periode: p.periode,
    a_temps: enPourcent(p.taux_livraison_a_temps),
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={lignes} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="periode" tick={{ fontSize: 11 }} minTickGap={32} />
        <YAxis domain={[0, 100]} unit=" %" tick={{ fontSize: 11 }} width={48} />
        <Tooltip
          formatter={(valeur) => [`${valeur} %`, "Livraison à temps"]}
          labelFormatter={(periode) => `Semaine du ${periode}`}
        />
        <Line
          type="monotone"
          dataKey="a_temps"
          stroke="#0E9F8E"
          strokeWidth={2}
          dot={false}
          connectNulls={false}
          isAnimationActive={false}
        />
        {anomalies.map((a) => {
          const point = lignes.find((l) => l.periode === a.periode_debut);
          if (!point || point.a_temps == null) return null;
          return (
            <ReferenceDot key={a.id} x={point.periode} y={point.a_temps} r={6} fill="#DC2626" stroke="white" />
          );
        })}
      </LineChart>
    </ResponsiveContainer>
  );
}