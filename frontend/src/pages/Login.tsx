import { isAxiosError } from "axios";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { seConnecter } from "@/api/auth";

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [envoiEnCours, setEnvoiEnCours] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErreur(null);
    setEnvoiEnCours(true);
    try {
      await seConnecter(username, password);
      navigate("/", { replace: true });
    } catch (e) {
      if (isAxiosError(e) && e.response?.status === 401) {
        setErreur("Identifiants incorrects.");
      } else {
        setErreur("Serveur injoignable. Vérifiez que Django est lancé.");
      }
    } finally {
      setEnvoiEnCours(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4 rounded-lg bg-white p-6 shadow">
        <h1 className="text-xl font-semibold text-slate-900">Connexion</h1>

        <label className="block text-sm text-slate-700">
          Identifiant
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>

        <label className="block text-sm text-slate-700">
          Mot de passe
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>

        {erreur && (
          <p role="alert" className="text-sm text-red-600">
            {erreur}
          </p>
        )}

        <button
          type="submit"
          disabled={envoiEnCours}
          className="w-full rounded bg-slate-900 px-4 py-2 text-white disabled:opacity-50"
        >
          {envoiEnCours ? "Connexion…" : "Se connecter"}
        </button>
      </form>
    </main>
  );
}