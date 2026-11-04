import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TimePoint } from "@/api/types";

export function TimeseriesChart({ data, granularity = "week" }: { data: TimePoint[]; granularity?: "day" | "week" | "month" }) {
  const rows = data.map((d) => ({ ...d, a_temps: d.taux_livraison_a_temps == null ? null :
      d.taux_livraison_a_temps * 100 }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="periode" tick={{ fontSize: 11 }} />
        <YAxis unit=" %" domain={[0, 100]} tick={{ fontSize: 11 }} />
        <Tooltip formatter={(v: number) => `${v.toFixed(1)} %`} labelFormatter={(l) => `${granularity === "day" ? "Jour du" : granularity === "month" ? "Mois de" : "Semaine du"} ${l}`} />
        <Line type="monotone" dataKey="a_temps" name="Livraison à temps" stroke="#0E9F8E" strokeWidth={2} dot={false} connectNulls={false} />
      </LineChart>
    </ResponsiveContainer>
); }