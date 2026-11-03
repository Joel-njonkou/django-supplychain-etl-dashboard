import { isAxiosError } from "axios";

import { useAnomalies, useExplain } from "@/api/hooks";
import ExplanationCard from "@/components/ExplanationCard";
import QueryState from "@/components/QueryState";
import { formater } from "@/lib/format";

function dateFr(iso: string): string {
  const [annee, mois, jour] = iso.split("-");
  return `${jour}/${mois}/${annee}`;
}

export default function Anomalies() {
  const anomalies = useAnomalies("week");
  const explication = useExplain();

  function messageErreur(): string {
    if (isAxiosError(explication.error) && explication.error.response?.status === 403) {
      return "Droits insuffisants : seul un analyste peut demander une explication.";
    }
    return "L'explication a échoué. Réessayez.";
  }

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Anomalies de retards détectées</h1>
        <p className="text-sm text-slate-500">
          Semaines dont le taux de retard s'écarte fortement de celui des 8 semaines précédentes.
        </p>
      </div>

      <QueryState requete={anomalies} vide={(liste) => liste.length === 0}>
        {(liste) => (
          <div className="space-y-4">
            {liste.map((a) => {
              const enCours = explication.isPending && explication.variables?.id === a.id;
              const enErreur = explication.isError && explication.variables?.id === a.id;

              return (
                <article key={a.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <header className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="font-medium text-slate-900">
                        Semaine du {dateFr(a.periode_debut)} au {dateFr(a.periode_fin)}
                      </h2>
                      <p className="text-sm text-slate-500">
                        Retards {formater(a.taux_retard_pct / 100, "pct")} (habituel{" "}
                        {formater(a.reference_pct / 100, "pct")}) · z = {a.z_score.toLocaleString("fr-FR")} ·{" "}
                        {formater(a.volume, "entier")} expéditions
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={enCours}
                      onClick={() => explication.mutate({ id: a.id, forcer: a.explanation !== null })}
                      className="rounded-lg bg-teal-600 px-3 py-1.5 text-sm text-white hover:bg-teal-700 disabled:opacity-50"
                    >
                      {enCours ? "Analyse…" : a.explanation ? "Réexpliquer" : "Expliquer"}
                    </button>
                  </header>

                  {enErreur && (
                    <p role="alert" className="mt-2 text-sm text-red-600">
                      {messageErreur()}
                    </p>
                  )}

                  {a.explanation && <ExplanationCard explication={a.explanation} source={a.explanation_source} />}
                </article>
              );
            })}
          </div>
        )}
      </QueryState>

      <p className="text-xs text-slate-500">
        Les faits sont calculés par le système ; le texte n'est qu'une mise en mots, contrôlée automatiquement. Une
        explication reste une hypothèse à vérifier.
      </p>
    </section>
  );
}