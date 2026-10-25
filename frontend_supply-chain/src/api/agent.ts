import { api } from "./client";
import type { Filters } from "./types";

export interface BottleneckExplanation {
  titre: string;
  resume: string;
  hypothese_principale: string;
  confiance: "faible" | "moyenne" | "élevée";
  preuves: string[];
  goulots_prioritaires?: string[];
  hypothese_alternative: string;
  limites: string[];
  actions: string[];
}

export interface BottleneckEvidence {
  global: { volume: number; retards: number; taux_retard_pct: number };
  classement_par_volume_de_retards: Array<Record<string, string | number>>;
  classement_par_retards_en_exces: Array<Record<string, string | number>>;
  modes: Array<Record<string, string | number>>;
  part_variabilite_expliquee_pct: { transporteur: number; region: number };
  constats: Array<{ id: string; texte: string }>;
  note_cout: string;
}

export interface ExplainResponse {
  source: "llm" | "template" | "none";
  explanation: BottleneckExplanation | null;
  evidence: BottleneckEvidence | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatTraceItem {
  outil: string;
  arguments: Record<string, unknown>;
}

export interface ChatResponse {
  source: "llm" | "fallback" | "data";
  answer: string;
  trace: ChatTraceItem[];
  evidence?: unknown[];
}

export async function explainBottlenecks(filters: Filters, refresh = false): Promise<ExplainResponse> {
  const { date_min, date_max, region, transporteur } = filters;
  return (await api.post<ExplainResponse>(
    "/agent/bottlenecks/explain/",
    { date_min, date_max, region, transporteur },
    { params: refresh ? { refresh: "true" } : undefined },
  )).data;
}

export async function chat(question: string, history: ChatMessage[]): Promise<ChatResponse> {
  return (await api.post<ChatResponse>("/agent/chat/", { question, history })).data;
}
