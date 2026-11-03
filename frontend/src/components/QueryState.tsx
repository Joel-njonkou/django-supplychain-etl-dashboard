import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactNode } from "react";

interface Props<T> {
  requete: UseQueryResult<T>;
  vide?: (donnees: T) => boolean;
  children: (donnees: T) => ReactNode;
}

export default function QueryState<T>({ requete, vide, children }: Props<T>) {
  if (requete.isPending) {
    return <div aria-busy="true" className="h-24 animate-pulse rounded-xl bg-slate-200/60" />;
  }
  if (requete.isError) {
    return (
      <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Impossible de charger les données.{" "}
        <button type="button" onClick={() => requete.refetch()} className="underline">
          Réessayer
        </button>
      </div>
    );
  }
  if (vide?.(requete.data)) {
    return (
      <div className="rounded-xl bg-white p-6 text-center text-sm text-slate-500">
        Aucune donnée pour ces filtres.
      </div>
    );
  }
  return <>{children(requete.data)}</>;
}