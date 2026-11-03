import { useSearchParams } from "react-router-dom";

import type { Filters } from "@/api/types";

const CLES = ["date_min", "date_max", "region", "transporteur", "marche"] as const;

export function useFilters(): [Filters, (modifications: Partial<Filters>) => void] {
  const [parametres, setParametres] = useSearchParams();

  const filtres: Filters = {};
  for (const cle of CLES) {
    const valeur = parametres.get(cle);
    if (valeur) filtres[cle] = valeur;
  }

  function modifier(modifications: Partial<Filters>) {
    const suivants = new URLSearchParams(parametres);
    for (const [cle, valeur] of Object.entries(modifications)) {
      if (valeur) suivants.set(cle, valeur);
      else suivants.delete(cle);
    }
    setParametres(suivants, { replace: true });
  }

  return [filtres, modifier];
}