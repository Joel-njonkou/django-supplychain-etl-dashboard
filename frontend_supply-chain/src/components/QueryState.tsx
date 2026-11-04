
import type { UseQueryResult } from "@tanstack/react-query";
import { Spinner } from "@/components/Spinner";

export function QueryState<T>({
  q,
  children,
  empty,
}: {
  q: UseQueryResult<T>;
  children: (data: T) => React.ReactNode;
  empty?: (data: T) => boolean;
}) {
  if (q.isPending) {
    return (
      <div className="query-loading" aria-busy="true">
        <Spinner label="Chargement des données…" size="large" />
      </div>
    );
  }
  if (q.isError && q.data === undefined) {
    return (
      <div role="alert" className="query-error">
        <span>Impossible de charger les données.</span>
        <button className="text-button" onClick={() => q.refetch()}>Réessayer</button>
      </div>
    );
  }
  if (q.data === undefined) return null;
  if (empty?.(q.data)) {
    return (
      <div className="query-empty">
        {q.isFetching && <Spinner label="Actualisation…" size="small" />}
        {!q.isFetching && "Aucune donnée pour ces filtres."}
      </div>
    );
  }
  return (
    <div className="query-result" aria-busy={q.isFetching}>
      {q.isFetching && <div className="query-refresh"><Spinner label="Actualisation…" size="small" /></div>}
      {q.isError && (
        <div role="alert" className="query-error query-error-inline">
          <span>La dernière actualisation a échoué. Les données affichées peuvent être obsolètes.</span>
          <button className="text-button" onClick={() => q.refetch()}>Réessayer</button>
        </div>
      )}
      {children(q.data)}
    </div>
  );
}