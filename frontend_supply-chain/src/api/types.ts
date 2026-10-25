export interface Kpi {
    volume: number; retards: number;
    taux_retard: number | null; taux_livraison_a_temps: number | null;
    retard_moyen_jours: number | null; cout_moyen: number | null;
}
export interface TimePoint extends Kpi { periode: string }
export interface Bottleneck extends Kpi { region?: string; transporteur?: string }
export interface Filters { date_min?: string; date_max?: string; region?: string; transporteur?:
    string; marche?: string; statut_livraison?: string }
export interface Page<T> { count: number; next: string | null; previous: string | null; results: T[]
}
export interface Transporteur { id: number; code: string; nom: string }
export interface Entrepot { id: number; code: string; nom: string }
export interface Commande {
  id: number; order_id: number; date_commande: string; statut: string;
  segment_client: string; marche: string; region: string; pays: string; ville: string;
  nb_articles: number; montant_total: string; profit_total: string;
  expedition?: Expedition | null;
}
export interface Expedition {
  id: number; order_id: number; region: string; date_commande: string;
  transporteur: Transporteur; entrepot: Entrepot; date_expedition: string | null;
  delai_prevu_jours: number; delai_reel_jours: number; ecart_jours: number;
  statut_livraison: "a_temps" | "en_avance" | "en_retard" | "annulee";
  en_retard: boolean; cout_estime: string;
}
export interface EtlRun {
  id: number; started_at: string; finished_at: string | null;
  status: "running" | "success" | "failed"; source_file: string;
  rows_read: number; rows_rejected: number; commandes_loaded: number;
  expeditions_loaded: number; message: string;
}