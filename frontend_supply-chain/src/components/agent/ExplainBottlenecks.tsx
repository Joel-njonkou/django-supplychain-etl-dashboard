import { useMutation } from "@tanstack/react-query";
import type { Filters } from "@/api/types";
import { explainBottlenecks } from "@/api/agent";
import { agentErrorMessage } from "@/api/errors";
import { Spinner } from "@/components/Spinner";

const confidenceLabels = {
  faible: "Confiance faible",
  moyenne: "Confiance modérée",
  élevée: "Confiance élevée",
};

function ListBlock({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <section className="agent-list-block">
      <h3>{title}</h3>
      <ul>{items.map((item, index) => <li key={`${title}-${index}`}>{item}</li>)}</ul>
    </section>
  );
}

export function ExplainBottlenecks({ filters }: { filters: Filters }) {
  const analysis = useMutation({ mutationFn: (refresh: boolean) => explainBottlenecks(filters, refresh) });
  const result = analysis.data;
  const explanation = result?.explanation;

  return (
    <section className="panel explain-panel">
      <div className="explain-heading">
        <div className="explain-heading-copy">
          <span className="agent-icon" aria-hidden="true">✦</span>
          <div>
            <p className="eyebrow">ANALYSE ASSISTÉE</p>
            <h2>Comprendre les goulots d’étranglement</h2>
            <p className="muted">Une lecture des retards selon les filtres actifs du tableau de bord.</p>
          </div>
        </div>
        <button
          className="button button-primary explain-button"
          disabled={analysis.isPending}
          onClick={() => analysis.mutate(Boolean(explanation))}
        >
          {analysis.isPending
            ? <Spinner label="Analyse en cours…" size="small" />
            : explanation ? "Actualiser l’analyse" : "Expliquer"}
        </button>
      </div>

      {analysis.isError && (
        <div className="agent-error" role="alert">
          <span>{agentErrorMessage(analysis.error)}</span>
          <button className="text-button" onClick={() => analysis.mutate(Boolean(explanation))}>Réessayer</button>
        </div>
      )}

      {result?.source === "none" && (
        <div className="agent-empty">Aucune expédition ne correspond aux filtres sélectionnés. Modifiez les filtres puis relancez l’analyse.</div>
      )}

      {explanation && (
        <div className="explain-result">
          <div className="explain-result-meta">
            <span className={`confidence-badge confidence-${explanation.confiance}`}>{confidenceLabels[explanation.confiance]}</span>
            <span className="agent-source">{result.source === "llm" ? "IA · données vérifiées" : "Analyse automatique · mode de secours"}</span>
          </div>
          <h3 className="explain-title">{explanation.titre}</h3>
          <p className="explain-summary">{explanation.resume}</p>
          <div className="explain-hypothesis"><strong>Hypothèse principale</strong><p>{explanation.hypothese_principale}</p></div>
          <ListBlock title="Goulots prioritaires — retards en excès" items={explanation.goulots_prioritaires} />
          <ListBlock title="Éléments observés" items={explanation.preuves} />
          <ListBlock title="Actions suggérées" items={explanation.actions} />
          <details className="agent-details">
            <summary>Hypothèse alternative et limites</summary>
            <p>{explanation.hypothese_alternative}</p>
            <ListBlock title="Limites de l’analyse" items={explanation.limites} />
          </details>
          {result.evidence && (
            <div className="agent-evidence">
              <span>Base de l’analyse</span>
              <strong>{result.evidence.global.volume.toLocaleString("fr-FR")} expéditions</strong>
              <strong>{result.evidence.global.taux_retard_pct.toFixed(1)} % de retards</strong>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
