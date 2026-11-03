const nombre = (options: Intl.NumberFormatOptions) => new Intl.NumberFormat("fr-FR", options);

export const FORMATS = {
  pct: (v: number) =>
    nombre({ style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(v),
  jours: (v: number) => `${nombre({ maximumFractionDigits: 1 }).format(v)} j`,
  euros: (v: number) => nombre({ style: "currency", currency: "EUR" }).format(v),
  entier: (v: number) => nombre({}).format(v),
};

export type Format = keyof typeof FORMATS;

export function formater(valeur: number | null | undefined, format: Format): string {
  return valeur == null ? "—" : FORMATS[format](valeur);
}