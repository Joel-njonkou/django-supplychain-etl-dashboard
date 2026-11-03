import { useAnomalies, useBottlenecks, useSummary, useTimeseries, useTransporteurs } from "@/api/hooks";
import CarrierBars from "@/components/charts/CarrierBars";
import TimeseriesChart from "@/components/charts/TimeseriesChart";
import FilterBar from "@/components/FilterBar";
import KpiCard from "@/components/KpiCard";
import QueryState from "@/components/QueryState";
import { formater } from "@/lib/format";
import { useFilters } from "@/state/filters";

const CADRE = "rounded-xl border border-slate-200 bg-white p-4 shadow-sm";

export default function Dashboard() {
  const [filtres, modifierFiltres] = useFilters();
  const resume = useSummary(filtres);
  const serie = useTimeseries(filtres, "week");
  const anomalies = useAnomalies("week");
  const parTransporteur = useBottlenecks(filtres, "transporteur", 10);
  const transporteurs = useTransporteurs();

  const nomActif = transporteurs.data?.find((t) => t.code === filtres.transporteur)?.nom;

  function choisirTransporteur(nom: string) {
    const code = transporteurs.data?.find((t) => t.nom === nom)?.code;
    modifierFiltres({ transporteur: code === filtres.transporteur ? undefined : code });
  }

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
            <KpiCard libelle="Retard moyen" valeur={k.retard_moyen_jours} format="jours" aide="Sur les expéditions en retard" />
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

      <div className="grid gap-4 lg:grid-cols-3">
        <section className={`${CADRE} lg:col-span-2`}>
          <h2 className="mb-2 text-sm font-medium text-slate-700">Évolution du taux de livraison à temps (par semaine)</h2>
          <QueryState requete={serie} vide={(points) => points.length === 0}>
            {(points) => <TimeseriesChart points={points} anomalies={anomalies.data ?? []} />}
          </QueryState>
          <p className="mt-2 text-xs text-slate-500">
            <span className="text-red-600">●</span> Semaine anormale détectée par l'agent
          </p>
        </section>

        <section className={CADRE}>
          <h2 className="mb-2 text-sm font-medium text-slate-700">Taux de retard par transporteur</h2>
          <QueryState requete={parTransporteur} vide={(lignes) => lignes.length === 0}>
            {(lignes) => <CarrierBars lignes={lignes} actif={nomActif} onChoisir={choisirTransporteur} />}
          </QueryState>
          <p className="mt-2 text-xs text-slate-500">Cliquez sur une barre pour filtrer, à nouveau pour annuler.</p>
        </section>
      </div>
    </div>
  );
}