import type { Explanation } from "@/api/types";

interface Props {
  explication: Explanation;
  source: "llm" | "template" | "";
}

const COULEURS_CONFIANCE: Record<Explanation["confiance"], string> = {
  faible: "bg-amber-100 text-amber-800",
  moyenne: "bg-sky-100 text-sky-800",
  élevée: "bg-emerald-100 text-emerald-800",
};

export default function ExplanationCard({ explication, source }: Props) {
  const gardeFous = explication._garde_fous ?? [];

  return (
    <div className="mt-4 space-y-3 border-t border-slate-100 pt-4 text-sm text-slate-700">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-medium text-slate-900">{explication.titre}</h3>
        <span className={`rounded-full px-2 py-0.5 text-xs ${COULEURS_CONFIANCE[explication.confiance]}`}>
          Confiance {explication.confiance}
        </span>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
          {source === "llm" ? "Rédigé par le modèle de langage" : "Gabarit de secours"}
        </span>
      </div>

      <p>{explication.resume}</p>

      <p>
        <span className="font-medium text-slate-900">Hypothèse : </span>
        {explication.hypothese}
      </p>

      <div>
        <h4 className="font-medium text-slate-900">Preuves chiffrées</h4>
        <ul className="mt-1 list-disc space-y-1 pl-5">
          {explication.preuves.map((preuve) => (
            <li key={preuve}>{preuve}</li>
          ))}
        </ul>
      </div>

      <details>
        <summary className="cursor-pointer font-medium text-slate-900">Hypothèse alternative</summary>
        <p className="mt-1">{explication.hypothese_alternative}</p>
      </details>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <h4 className="font-medium text-slate-900">Limites</h4>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {explication.limites.map((limite) => (
              <li key={limite}>{limite}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="font-medium text-slate-900">Vérifications suggérées</h4>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {explication.verifications.map((verification) => (
              <li key={verification}>{verification}</li>
            ))}
          </ul>
        </div>
      </div>

      {gardeFous.length > 0 && (
        <p className="text-xs text-slate-500">Gabarit utilisé car : {gardeFous.join(" ; ")}.</p>
      )}
    </div>
  );
}