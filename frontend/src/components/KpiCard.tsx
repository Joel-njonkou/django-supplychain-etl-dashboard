import { type Format, formater } from "@/lib/format";

interface Props {
  libelle: string;
  valeur: number | null | undefined;
  format: Format;
  aide?: string;
}

export default function KpiCard({ libelle, valeur, format, aide }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{libelle}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{formater(valeur, format)}</div>
      {aide && <div className="mt-1 text-xs text-slate-400">{aide}</div>}
    </div>
  );
}