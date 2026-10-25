import { isAxiosError } from "axios";

export function agentErrorMessage(error: unknown): string {
  if (!isAxiosError(error)) {
    return "Une erreur inattendue a interrompu la requête. Réessayez.";
  }

  const status = error.response?.status;
  if (status === undefined) {
    return "Impossible de joindre l’API Django. Vérifiez que le serveur fonctionne sur le port 8000.";
  }
  if (status === 401) {
    return "Votre session a expiré. Reconnectez-vous pour continuer.";
  }
  if (status === 403) {
    return "Votre compte n’est pas autorisé à utiliser cet endpoint.";
  }
  if (status === 404) {
    return "Endpoint agent introuvable (404). Redémarrez Django depuis le dossier backend_supply-chain pour charger ses routes.";
  }
  if (status === 429) {
    return "Trop de requêtes vers l’assistant. Attendez une minute puis réessayez.";
  }

  const body: unknown = error.response.data;
  if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
    return body.detail;
  }
  if (status >= 500) {
    return `Le serveur Django a rencontré une erreur (HTTP ${status}). Consultez le terminal du backend puis réessayez.`;
  }
  return `La requête a échoué (HTTP ${status}). Vérifiez les données envoyées puis réessayez.`;
}
