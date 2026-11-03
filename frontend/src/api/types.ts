export interface Kpi {
  volume: number;
  retards: number;
  taux_retard: number | null;
  taux_livraison_a_temps: number | null;
  retard_moyen_jours: number | null;
  cout_moyen: number | null;
}

export interface TimePoint extends Kpi {
  periode: string;
}

export interface Bottleneck extends Kpi {
  region?: string;
  transporteur?: string;
}

export interface Filters {
  date_min?: string;
  date_max?: string;
  region?: string;
  transporteur?: string;
  marche?: string;
}

export interface Explanation {
  titre: string;
  resume: string;
  hypothese: string;
  confiance: "faible" | "moyenne" | "élevée";
  preuves: string[];
  hypothese_alternative: string;
  limites: string[];
  verifications: string[];
  _garde_fous?: string[];
}

export interface Anomaly {
  id: number;
  granularite: string;
  periode_debut: string;
  periode_fin: string;
  taux_retard_pct: number;
  reference_pct: number;
  z_score: number;
  volume: number;
  explanation: Explanation | null;
  explanation_source: "llm" | "template" | "";
  created_at: string;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Transporteur {
  id: number;
  code: string;
  nom: string;
}