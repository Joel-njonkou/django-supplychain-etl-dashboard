import { api, tokens } from "@/api/client";

export async function seConnecter(username: string, password: string): Promise<void> {
  const reponse = await api.post<{ access: string; refresh: string }>("/auth/token/", {
    username,
    password,
  });
  tokens.set(reponse.data.access, reponse.data.refresh);
}