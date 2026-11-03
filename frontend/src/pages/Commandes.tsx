import { useState } from "react";

import { useExpeditions } from "@/api/hooks";
import type { Expedition, Filters } from "@/api/types";
import FilterBar from "@/components/FilterBar";
import QueryState from "@/components/QueryState";
import { formater } from "@/lib/format";
import { useFilters } from "@/state/filters";

const STATUTS: Record<Expedition["statut_livraison"], { libelle: string; classes: string }> = {
  a_temps: { libelle: "À temps", classes: "bg-emerald-100 text-emerald-800" },
  en_avance: { libelle: "En avance", classes: "bg-sky-100 text-sky-800" },
  en_retard: { libelle: "En retard", classes: "bg-red-100 text-red-800" },
  annulee: { libelle: "Annulée", classes: "bg-slate-100 text-slate-600" },
};

const TRIS = [
  { valeur: "id", libelle: "Ordre de chargement" },
  { valeur: "-ecart_jours", libelle: "Plus gros retards d'abord" },
  { valeur: "ecart_jours", libelle: "Plus en avance d'abord" },
  { valeur: "-cout_estime", libelle: "Coût estimé décroissant" },
  { valeur: "cout_estime", libelle: "Coût estimé croissant" },
];

const TAILLES = [25, 50, 100];

const CHAMP = "rounded border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900";

export default function Commandes() {
  const [filtres, modifierFiltres] = useFilters();
  const [page, setPage] = useState(1);
  const [taille, setTaille] = useState(25);
  const [tri, setTri] = useState("id");
  const expeditions = useExpeditions(filtres, page, taille, tri);

  function changerFiltres(modifications: Partial<Filters>) {
    setPage(1);
    modifierFiltres(modifications);
  }

  return (
    <section className="space-y-4">
      <h1 className="text-xl font-semibold text-slate-900">Commandes et expéditions</h1>

      <FilterBar filtres={filtres} onChange={changerFiltres} />

      <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
        <label className="flex items-center gap-2">
          Trier par
          <select
            value={tri}
            onChange={(e) => {
              setTri(e.target.value);
              setPage(1);
            }}
            className={CHAMP}
          >
            {TRIS.map((t) => (
              <option key={t.valeur} value={t.valeur}>
                {t.libelle}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2">
          Lignes par page
          <select
            value={taille}
            onChange={(e) => {
              setTaille(Number(e.target.value));
              setPage(1);
            }}
            className={CHAMP}
          >
            {TAILLES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </div>

      <QueryState requete={expeditions} vide={(resultat) => resultat.count === 0}>
        {(resultat) => {
          const nombrePages = Math.max(1, Math.ceil(resultat.count / taille));
          return (
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                      <th scope="col" className="px-3 py-2 font-medium">N° commande</th>
                      <th scope="col" className="px-3 py-2 font-medium">Date</th>
                      <th scope="col" className="px-3 py-2 font-medium">Région</th>
                      <th scope="col" className="px-3 py-2 font-medium">Transporteur</th>
                      <th scope="col" className="px-3 py-2 font-medium">Statut</th>
                      <th scope="col" className="px-3 py-2 text-right font-medium">Écart (jours)</th>
                      <th scope="col" className="px-3 py-2 text-right font-medium">Coût estimé</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resultat.results.map((e) => (
                      <tr key={e.id} className="border-b border-slate-100">
                        <td className="px-3 py-1.5 tabular-nums">{e.order_id}</td>
                        <td className="px-3 py-1.5 tabular-nums">{e.date_commande.slice(0, 10)}</td>
                        <td className="px-3 py-1.5">{e.region}</td>
                        <td className="px-3 py-1.5">{e.transporteur.nom}</td>
                        <td className="px-3 py-1.5">
                          <span className={`rounded-full px-2 py-0.5 text-xs ${STATUTS[e.statut_livraison].classes}`}>
                            {STATUTS[e.statut_livraison].libelle}
                          </span>
                        </td>
                        <td className="px-3 py-1.5 text-right tabular-nums">{e.ecart_jours ?? "—"}</td>
                        <td className="px-3 py-1.5 text-right tabular-nums">{formater(Number(e.cout_estime), "euros")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm text-slate-600">
                <span>
                  {formater(resultat.count, "entier")} expéditions · page {page} sur {formater(nombrePages, "entier")}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={!resultat.previous}
                    onClick={() => setPage((p) => p - 1)}
                    className="rounded border border-slate-300 px-3 py-1 disabled:opacity-40"
                  >
                    Précédent
                  </button>
                  <button
                    type="button"
                    disabled={!resultat.next}
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded border border-slate-300 px-3 py-1 disabled:opacity-40"
                  >
                    Suivant
                  </button>
                </div>
              </div>
            </div>
          );
        }}
      </QueryState>
    </section>
  );
}