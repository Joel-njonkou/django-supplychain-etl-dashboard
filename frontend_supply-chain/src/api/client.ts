import axios, { type InternalAxiosRequestConfig } from "axios";

const ACCESS = "access_token";
const REFRESH = "refresh_token";

declare module "axios" {
  interface InternalAxiosRequestConfig {
    _retry?: boolean;
  }
}

export const api = axios.create({ baseURL: "/api/v1" });
export const tokens = {
  get: () => localStorage.getItem(ACCESS),
  set: (access: string, refresh?: string) => {
    localStorage.setItem(ACCESS, access);
    if (refresh) localStorage.setItem(REFRESH, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
};

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const access = tokens.get();
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

let refreshInFlight: Promise<string> | undefined;

api.interceptors.response.use(undefined, async (error: unknown) => {
  if (!axios.isAxiosError(error) || error.response?.status !== 401 || !error.config) {
    return Promise.reject(error);
  }
  const request = error.config;
  if (request.url?.includes("/auth/")) {
    return Promise.reject(error);
  }
  const refresh = localStorage.getItem(REFRESH);
  if (!refresh || request._retry) {
    tokens.clear();
    if (window.location.pathname !== "/login") window.location.assign("/login");
    return Promise.reject(error);
  }
  request._retry = true;
  refreshInFlight ??= axios.post<{ access: string }>("/api/v1/auth/token/refresh/", { refresh })
    .then(({ data }) => data.access)
    .finally(() => { refreshInFlight = undefined; });
  try {
    const access = await refreshInFlight;
    tokens.set(access);
    request.headers.Authorization = `Bearer ${access}`;
    return api(request);
  } catch (refreshError) {
    tokens.clear();
    if (window.location.pathname !== "/login") window.location.assign("/login");
    return Promise.reject(refreshError);
  }
});
