import { useSummary } from "@/api/hooks";
import FilterBar from "@/components/FilterBar";
import KpiCard from "@/components/KpiCard";
import QueryState from "@/components/QueryState";
import { formater } from "@/lib/format";
import { useFilters } from "@/state/filters";

export default function Dashboard() {
  const [filtres, modifierFiltres] = useFilters();
  const resume = useSummary(filtres);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-900">Tableau de bord</h1>

      <FilterBar filtres={filtres} onChange={modifierFiltres} />

      <QueryState requete={resume} vide={(k) => k.volume === 0}>
        {(k) => (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              libelle="Livraison à temps"
              valeur={k.taux_livraison_a_temps}
              format="pct"
              aide={`Taux de retard : ${formater(k.taux_retard, "pct")}`}
            />
            <KpiCard
              libelle="Retard moyen"
              valeur={k.retard_moyen_jours}
              format="jours"
              aide="Sur les expéditions en retard"
            />
            <KpiCard
              libelle="Coût moyen / expédition (estimé)"
              valeur={k.cout_moyen}
              format="euros"
              aide="Grille tarifaire, pas un coût réel"
            />
            <KpiCard
              libelle="Volume"
              valeur={k.volume}
              format="entier"
              aide={`${formater(k.retards, "entier")} en retard · hors annulations`}
            />
          </div>
        )}
      </QueryState>
    </div>
  );
}