import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

const ACCESS = "access_token";
const REFRESH = "refresh_token";

export const tokens = {
  getAccess: () => localStorage.getItem(ACCESS),
  getRefresh: () => localStorage.getItem(REFRESH),
  set: (access: string, refresh?: string) => {
    localStorage.setItem(ACCESS, access);
    if (refresh) localStorage.setItem(REFRESH, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
};

export const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((config) => {
  const access = tokens.getAccess();
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

type RequeteRejouable = InternalAxiosRequestConfig & { _rejouee?: boolean };

let rafraichissement: Promise<string> | null = null;

function rafraichirJeton(refresh: string): Promise<string> {
  rafraichissement ??= axios
    .post<{ access: string }>("/api/v1/auth/token/refresh/", { refresh })
    .then((reponse) => reponse.data.access)
    .finally(() => {
      rafraichissement = null;
    });
  return rafraichissement;
}

api.interceptors.response.use(
  (reponse) => reponse,
  async (erreur: AxiosError) => {
    const requete = erreur.config as RequeteRejouable | undefined;
    const refresh = tokens.getRefresh();
    const estAuthentification = requete?.url?.includes("/auth/") ?? false;

    if (erreur.response?.status === 401 && requete && refresh && !requete._rejouee && !estAuthentification) {
      requete._rejouee = true;
      try {
        const access = await rafraichirJeton(refresh);
        tokens.set(access);
        requete.headers.Authorization = `Bearer ${access}`;
        return api(requete);
      } catch {
        tokens.clear();
        window.location.assign("/login");
      }
    }
    return Promise.reject(erreur);
  },
);