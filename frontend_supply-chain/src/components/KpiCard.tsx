
type Props = { label: string; value: number | null | undefined; format: "pct" | "days" | "money" | "int"; hint?: string };
  const nf = (o: Intl.NumberFormatOptions) => new Intl.NumberFormat("fr-FR", o);
  const FORMATS = {
    pct: (v: number) => nf({ style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1
        }).format(v),
    days: (v: number) => `${nf({ maximumFractionDigits: 1 }).format(v)} j`,
    money: (v: number) => nf({ style: "currency", currency: "EUR" }).format(v),
    int: (v: number) => nf({}).format(v),
};

export function KpiCard({ label, value, format, hint }: Props) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
        <div className="mt-1 text-2xl font-semibold text-slate-900">
            {value == null ? "—" : FORMATS[format](value)}               {/* null = aucune donnée, pas 0
               */}
    </div>
        {hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}
    </div>
); }
 