import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useBottlenecks, useCommandes, useEntrepots, useEtlRuns, useExpeditions, useSummary, useTimeseries, useTransporteurs } from "@/api/hooks";
import type { Filters, Page } from "@/api/types";
import { BottleneckHeatmap } from "@/components/BottleneckHeatmap";
import { KpiCard } from "@/components/KpiCard";
import { QueryState } from "@/components/QueryState";
import { Spinner } from "@/components/Spinner";
import { TimeseriesChart } from "@/components/TimeseriesChart";
import { ExplainBottlenecks } from "@/components/agent/ExplainBottlenecks";

const money = (value: string | number | null | undefined) => value == null ? "—" : new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(Number(value));
const date = (value: string | null | undefined) => value ? new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(new Date(value)) : "—";
const dateTime = (value: string | null | undefined) => value ? new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
const pct = (value: number | null | undefined) => value == null ? "—" : `${(value * 100).toFixed(1)} %`;

function PageHeading({ eyebrow, title, subtitle, action }: { eyebrow: string; title: string; subtitle: string; action?: React.ReactNode }) {
  return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="muted">{subtitle}</p></div>{action}</div>;
}

function FilterBar({ filters, update, includeCarrier = true, includeDelivery = true, includeMarket = false }: { filters: Filters; update: (patch: Partial<Filters>) => void; includeCarrier?: boolean; includeDelivery?: boolean; includeMarket?: boolean }) {
  const carriers = useTransporteurs();
  return (
    <div className="filter-bar">
      <label>Du<input type="date" value={filters.date_min ?? ""} onChange={(event) => update({ date_min: event.target.value || undefined })} /></label>
      <label>Au<input type="date" value={filters.date_max ?? ""} onChange={(event) => update({ date_max: event.target.value || undefined })} /></label>
      <label>Région<input placeholder="Toutes les régions" value={filters.region ?? ""} onChange={(event) => update({ region: event.target.value || undefined })} /></label>
      {includeMarket && <label>Marché<input placeholder="Tous les marchés" value={filters.marche ?? ""} onChange={(event) => update({ marche: event.target.value || undefined })} /></label>}
      {includeCarrier && <label>Transporteur<span className="filter-select">{carriers.isFetching && <Spinner label="Chargement" size="small" />}<select value={filters.transporteur ?? ""} onChange={(event) => update({ transporteur: event.target.value || undefined })}><option value="">Tous</option>{carriers.data?.map((item) => <option key={item.id} value={item.code}>{item.nom}</option>)}</select></span></label>}
      {includeDelivery && <label>Livraison<select value={filters.statut_livraison ?? ""} onChange={(event) => update({ statut_livraison: event.target.value || undefined })}><option value="">Tous les statuts</option><option value="en_retard">En retard</option><option value="a_temps">À temps</option><option value="en_avance">En avance</option><option value="annulee">Annulée</option></select></label>}
      <button className="button button-quiet" onClick={() => update({ date_min: undefined, date_max: undefined, region: undefined, transporteur: undefined, statut_livraison: undefined, marche: undefined })}>Effacer</button>
    </div>
  );
}

function useUrlFilters(): [Filters, (patch: Partial<Filters>) => void] {
  const [search, setSearch] = useSearchParams();
  const filters: Filters = {
    date_min: search.get("date_min") ?? undefined,
    date_max: search.get("date_max") ?? undefined,
    region: search.get("region") ?? undefined,
    transporteur: search.get("transporteur") ?? undefined,
    statut_livraison: search.get("statut_livraison") ?? undefined,
  };
  const update = (patch: Partial<Filters>) => {
    const next = new URLSearchParams(search);
    for (const [key, value] of Object.entries(patch)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    setSearch(next, { replace: true });
  };
  return [filters, update];
}

export function Dashboard() {
  const [filters, update] = useUrlFilters();
  const summary = useSummary(filters);
  const [granularity, setGranularity] = useState<"day" | "week" | "month">("week");
  const [breakdown, setBreakdown] = useState<"region" | "transporteur" | "region_transporteur">("region_transporteur");
  const [minVolume, setMinVolume] = useState(100);
  const series = useTimeseries(filters, granularity);
  const [limit, setLimit] = useState(10);
  const heatmap = useBottlenecks(filters, "region_transporteur", 100, minVolume);
  const report = useBottlenecks(filters, breakdown, limit, minVolume);
  return (
    <div className="page-stack">
      <PageHeading eyebrow="VUE D’ENSEMBLE" title="Performance logistique" subtitle="Suivez les retards, les coûts et les performances de livraison." />
      <FilterBar filters={filters} update={update} />
      <QueryState q={summary}>{(data) => <div className="kpi-grid"><KpiCard label="Expéditions suivies" value={data.volume} format="int" hint="Hors commandes annulées" /><KpiCard label="Expéditions en retard" value={data.retards} format="int" /><KpiCard label="Taux de retard" value={data.taux_retard} format="pct" /><KpiCard label="Retard moyen" value={data.retard_moyen_jours} format="days" /><KpiCard label="Coût estimé moyen" value={data.cout_moyen} format="money" /></div>}</QueryState>
      <div className="dashboard-grid">
        <section className="panel chart-panel"><div className="panel-heading"><div><h2>Livraisons à temps</h2><p>Évolution {granularity === "day" ? "journalière" : granularity === "week" ? "hebdomadaire" : "mensuelle"}</p></div><div className="panel-controls"><select aria-label="Granularité temporelle" value={granularity} onChange={(event) => setGranularity(event.target.value as "day" | "week" | "month")}><option value="day">Jour</option><option value="week">Semaine</option><option value="month">Mois</option></select><span className="legend-dot">● À temps</span></div></div><QueryState q={series} empty={(data) => !data.length}>{(data) => <TimeseriesChart data={data} granularity={granularity} />}</QueryState></section>
        <section className="panel"><div className="panel-heading"><div><h2>Points de congestion</h2><p>Régions et transporteurs à surveiller</p></div></div><QueryState q={heatmap} empty={(data) => !data.length}>{(data) => <BottleneckHeatmap rows={data} onPick={(region, transporteur) => update({ region, transporteur: transporteur.toLowerCase().replaceAll(" ", "-") })} />}</QueryState></section>
      </div>
      <ExplainBottlenecks
        key={JSON.stringify([filters.date_min, filters.date_max, filters.region, filters.transporteur])}
        filters={filters}
      />
      <section className="panel bottleneck-table"><div className="panel-heading"><div><h2>Principaux goulets d’étranglement</h2><p>Classement par volume de retards</p></div><div className="panel-controls"><select aria-label="Regrouper par" value={breakdown} onChange={(event) => setBreakdown(event.target.value as "region" | "transporteur" | "region_transporteur")}><option value="region_transporteur">Région et transporteur</option><option value="region">Région</option><option value="transporteur">Transporteur</option></select><select aria-label="Volume minimum" value={minVolume} onChange={(event) => setMinVolume(Number(event.target.value))}><option value={1}>1+ expédition</option><option value={30}>30+ expéditions</option><option value={100}>100+ expéditions</option></select><select aria-label="Nombre de résultats" value={limit} onChange={(event) => setLimit(Number(event.target.value))}><option value={5}>5 résultats</option><option value={10}>10 résultats</option><option value={25}>25 résultats</option></select></div></div>
        <QueryState q={report} empty={(data) => !data.length}>{(data) => <div className="table-wrap"><table><thead><tr><th>Région</th><th>Transporteur</th><th>Expéditions</th><th>Retards</th><th>Taux</th><th>Coût moyen</th></tr></thead><tbody>{data.map((item, index) => <tr key={`${item.region}-${item.transporteur}-${index}`}><td>{item.region ?? "—"}</td><td>{item.transporteur ?? "—"}</td><td>{item.volume}</td><td>{item.retards}</td><td><span className="status-pill status-warning">{pct(item.taux_retard)}</span></td><td>{money(item.cout_moyen)}</td></tr>)}</tbody></table></div>}</QueryState>
      </section>
    </div>
  );
}

function Pager<T>({ data, page, setPage }: { data: Page<T>; page: number; setPage: (page: number) => void }) {
  const pages = Math.max(1, Math.ceil(data.count / 25));
  return <div className="pager"><span>{data.count.toLocaleString("fr-FR")} résultats · page {page} sur {pages}</span><div><button className="button button-quiet" disabled={!data.previous} onClick={() => setPage(page - 1)}>← Précédent</button><button className="button button-quiet" disabled={!data.next} onClick={() => setPage(page + 1)}>Suivant →</button></div></div>;
}

export function Commandes() {
  const [filters, update] = useUrlFilters();
  const [page, setPage] = useState(1);
  const query = useCommandes(page, filters);
  return <div className="page-stack"><PageHeading eyebrow="OPÉRATIONS" title="Commandes" subtitle="Parcourez les commandes et leur état de traitement." /><FilterBar filters={filters} includeCarrier={false} includeDelivery={false} includeMarket update={(patch) => { setPage(1); update(patch); }} /><section className="panel"><QueryState q={query} empty={(data) => data.results.length === 0}>{(data) => <><div className="table-wrap"><table><thead><tr><th>Commande</th><th>Date</th><th>Statut</th><th>Marché</th><th>Région</th><th>Articles</th><th>Montant</th><th>Profit</th></tr></thead><tbody>{data.results.map((row) => <tr key={row.id}><td><Link className="table-link" to={`/commandes/${row.id}`}>#{row.order_id} ↗</Link></td><td>{date(row.date_commande)}</td><td><span className="status-pill">{row.statut}</span></td><td>{row.marche}</td><td>{row.region}</td><td>{row.nb_articles}</td><td>{money(row.montant_total)}</td><td>{money(row.profit_total)}</td></tr>)}</tbody></table></div><Pager data={data} page={page} setPage={setPage} /></>}</QueryState></section></div>;
}

export function Expeditions() {
  const [filters, update] = useUrlFilters();
  const [page, setPage] = useState(1);
  const query = useExpeditions(page, filters);
  return <div className="page-stack"><PageHeading eyebrow="OPÉRATIONS" title="Expéditions" subtitle="Suivez les délais réels, les coûts et les statuts de livraison." /><FilterBar filters={filters} update={(patch) => { setPage(1); update(patch); }} /><section className="panel"><QueryState q={query} empty={(data) => data.results.length === 0}>{(data) => <><div className="table-wrap"><table><thead><tr><th>Commande</th><th>Région</th><th>Transporteur</th><th>Entrepôt</th><th>Date d’envoi</th><th>Prévu / réel</th><th>Écart</th><th>Statut</th><th>Coût estimé</th></tr></thead><tbody>{data.results.map((row) => <tr key={row.id}><td><Link className="table-link" to={`/expeditions/${row.id}`}>#{row.order_id} ↗</Link></td><td>{row.region}</td><td>{row.transporteur.nom}</td><td>{row.entrepot.nom}</td><td>{date(row.date_expedition)}</td><td>{row.delai_prevu_jours} j / {row.delai_reel_jours} j</td><td className={row.ecart_jours > 0 ? "text-danger" : ""}>{row.ecart_jours > 0 ? "+" : ""}{row.ecart_jours} j</td><td><span className={`status-pill ${row.en_retard ? "status-warning" : "status-success"}`}>{row.statut_livraison.replaceAll("_", " ")}</span></td><td>{money(row.cout_estime)}</td></tr>)}</tbody></table></div><Pager data={data} page={page} setPage={setPage} /></>}</QueryState></section></div>;
}

export function Transporteurs() {
  const query = useTransporteurs();
  return <div className="page-stack"><PageHeading eyebrow="RÉFÉRENTIELS" title="Transporteurs" subtitle="Transporteurs enregistrés dans la plateforme." /><section className="panel"><QueryState q={query} empty={(data) => !data.length}>{(data) => <div className="reference-grid">{data.map((item) => <Link className="reference-card" key={item.id} to={`/transporteurs/${item.id}`}><span className="reference-icon">◉</span><span><strong>{item.nom}</strong><small>Code : {item.code}</small></span><span className="card-arrow">↗</span></Link>)}</div>}</QueryState></section></div>;
}

export function Entrepots() {
  const query = useEntrepots();
  return <div className="page-stack"><PageHeading eyebrow="RÉFÉRENTIELS" title="Entrepôts" subtitle="Hubs logistiques utilisés dans les expéditions." /><section className="panel"><QueryState q={query} empty={(data) => !data.length}>{(data) => <div className="reference-grid">{data.map((item) => <Link className="reference-card" key={item.id} to={`/entrepots/${item.id}`}><span className="reference-icon">⌖</span><span><strong>{item.nom}</strong><small>Code : {item.code}</small></span><span className="card-arrow">↗</span></Link>)}</div>}</QueryState></section></div>;
}

export function EtlRuns() {
  const [page, setPage] = useState(1);
  const query = useEtlRuns(page);
  return <div className="page-stack"><PageHeading eyebrow="PIPELINE DE DONNÉES" title="Exécutions ETL" subtitle="Historique des imports et suivi de la qualité des données." /><section className="panel"><QueryState q={query} empty={(data) => data.results.length === 0}>{(data) => <><div className="table-wrap"><table><thead><tr><th>Démarrage</th><th>Statut</th><th>Fichier source</th><th>Lignes lues</th><th>Rejets</th><th>Commandes chargées</th><th>Expéditions chargées</th><th>Fin</th><th>Détails</th></tr></thead><tbody>{data.results.map((row) => <tr key={row.id}><td>{dateTime(row.started_at)}</td><td><span className={`status-pill ${row.status === "success" ? "status-success" : row.status === "failed" ? "status-error" : ""}`}>{row.status}</span></td><td className="source-file">{row.source_file}</td><td>{row.rows_read.toLocaleString("fr-FR")}</td><td>{row.rows_rejected.toLocaleString("fr-FR")}</td><td>{row.commandes_loaded.toLocaleString("fr-FR")}</td><td>{row.expeditions_loaded.toLocaleString("fr-FR")}</td><td>{dateTime(row.finished_at)}</td><td><Link className="table-link" to={`/etl/runs/${row.id}`}>Voir ↗</Link></td></tr>)}</tbody></table></div><Pager data={data} page={page} setPage={setPage} /></>}</QueryState></section></div>;
}

const detailLabels: Record<string, string> = {
  id: "Identifiant", order_id: "Commande", date_commande: "Date de commande", statut: "Statut",
  segment_client: "Segment client", marche: "Marché", region: "Région", pays: "Pays", ville: "Ville",
  nb_articles: "Nombre d’articles", montant_total: "Montant total", profit_total: "Profit total",
  date_expedition: "Date d’expédition", delai_prevu_jours: "Délai prévu", delai_reel_jours: "Délai réel",
  ecart_jours: "Écart de délai", statut_livraison: "Statut de livraison", en_retard: "En retard",
  cout_estime: "Coût estimé", code: "Code", nom: "Nom", started_at: "Démarrage", finished_at: "Fin",
  source_file: "Fichier source", rows_read: "Lignes lues", rows_rejected: "Lignes rejetées",
  commandes_loaded: "Commandes chargées", expeditions_loaded: "Expéditions chargées", message: "Rapport",
};

function formatDetail(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "boolean") return value ? "Oui" : "Non";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

export function RecordDetail({ endpoint, title }: { endpoint: string; title: string }) {
  const { id } = useParams();
  const query = useQuery({
    queryKey: ["record", endpoint, id],
    queryFn: async () => (await api.get<Record<string, unknown>>(`${endpoint}${id}/`)).data,
    enabled: Boolean(id),
  });
  return <div className="page-stack"><PageHeading eyebrow="DÉTAIL" title={`${title} ${id ? `#${id}` : ""}`} subtitle="Informations retournées par l’API." action={<Link className="button button-quiet" to="..">← Retour</Link>} /><section className="panel"><QueryState q={query}>{(record) => <dl className="detail-grid">{Object.entries(record).map(([key, value]) => <div key={key}><dt>{detailLabels[key] ?? key.replaceAll("_", " ")}</dt><dd className={typeof value === "object" && value ? "detail-json" : ""}>{formatDetail(value)}</dd></div>)}</dl>}</QueryState></section></div>;
}
