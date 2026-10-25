import { useState } from "react";
import { isAxiosError } from "axios";
import { Link, NavLink, Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { api, tokens } from "@/api/client";
import { Spinner } from "@/components/Spinner";
import { ChatPanel } from "@/components/agent/ChatPanel";
import { Dashboard, Entrepots, Expeditions, Commandes, Transporteurs, EtlRuns, RecordDetail } from "@/pages/DataPages";

function Login() {
  const navigate = useNavigate();
  const [registering, setRegistering] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const login = useMutation({
    mutationFn: async () => (await api.post<{ access: string; refresh: string }>("/auth/token/", { username, password })).data,
    onSuccess: ({ access, refresh }) => {
      tokens.set(access, refresh);
      navigate("/", { replace: true });
    },
  });
  const register = useMutation({
    mutationFn: async () => (await api.post<{ access: string; refresh: string }>("/auth/register/", {
      username,
      email,
      password,
      password_confirmation: passwordConfirmation,
    })).data,
    onSuccess: ({ access, refresh }) => {
      tokens.set(access, refresh);
      navigate("/", { replace: true });
    },
  });
  const pending = login.isPending || register.isPending;
  const error = registering ? register.error : login.error;

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (registering) register.mutate();
    else login.mutate();
  }

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={submit}>
        <div className="brand-mark">SC</div>
        <p className="eyebrow">Supply chain intelligence</p>
        <h1>{registering ? "Créer un compte" : "Connexion"}</h1>
        <p className="muted">{registering ? "Créez votre compte pour accéder au tableau de bord." : "Connectez-vous pour accéder au tableau de bord."}</p>
        <label>Nom d’utilisateur<input autoComplete="username" minLength={1} maxLength={150} required value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        {registering && <label>Adresse e-mail<input autoComplete="email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>}
        <label>Mot de passe<input autoComplete={registering ? "new-password" : "current-password"} type="password" minLength={registering ? 8 : undefined} required value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {registering && <label>Confirmer le mot de passe<input autoComplete="new-password" type="password" minLength={8} required value={passwordConfirmation} onChange={(event) => setPasswordConfirmation(event.target.value)} /></label>}
        {error && <p className="error-message" role="alert">{registrationError(error, registering)}</p>}
        <button className="button button-primary full-width" disabled={pending}>{pending ? <Spinner label={registering ? "Création du compte…" : "Connexion…"} size="small" /> : registering ? "Créer mon compte" : "Se connecter"}</button>
        <p className="auth-switch">{registering ? "Vous avez déjà un compte ?" : "Vous n’avez pas encore de compte ?"} <button className="text-button" type="button" onClick={() => { setRegistering((value) => !value); login.reset(); register.reset(); }}>{registering ? "Se connecter" : "Créer un compte"}</button></p>
      </form>
    </main>
  );
}

function registrationError(error: unknown, registering: boolean): string {
  if (isAxiosError(error)) {
    const body: unknown = error.response?.data;
    if (body && typeof body === "object") {
      const values = Object.values(body as Record<string, unknown>)
        .flatMap((value) => Array.isArray(value) ? value : [value])
        .filter((value): value is string => typeof value === "string");
      if (values.length) return values.join(" ");
    }
  }
  return registering ? "La création du compte a échoué. Vérifiez les informations et réessayez." : "Connexion impossible. Vérifiez vos identifiants et réessayez.";
}

function RequireAuth() {
  return tokens.get() ? <Outlet /> : <Navigate to="/login" replace />;
}

function Shell() {
  const navigate = useNavigate();
  const links = [
    ["/", "Vue d’ensemble", "⌂"],
    ["/commandes", "Commandes", "▤"],
    ["/expeditions", "Expéditions", "⇢"],
    ["/transporteurs", "Transporteurs", "◉"],
    ["/entrepots", "Entrepôts", "⌖"],
    ["/etl", "Exécutions ETL", "↻"],
  ];
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand"><span className="brand-mark">SC</span><span><strong>SupplyChain</strong><small>ANALYTICS</small></span></Link>
        <div className="nav-caption">ESPACE DE TRAVAIL</div>
        <nav>{links.map(([to, label, icon]) => <NavLink key={to} end={to === "/"} to={to} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}><span className="nav-icon">{icon}</span>{label}</NavLink>)}</nav>
        <div className="sidebar-footer"><span className="status-dot" /> API connectée</div>
      </aside>
      <main className="main-panel">
        <header className="topbar"><div><span className="eyebrow">PLATEFORME LOGISTIQUE</span><strong>Analyse de la chaîne d’approvisionnement</strong></div><button className="button button-quiet" onClick={() => { tokens.clear(); navigate("/login", { replace: true }); }}>Déconnexion <span aria-hidden="true">↗</span></button></header>
        <div className="page-content"><RoutesContent /></div>
      </main>
      <ChatPanel />
    </div>
  );
}

function RoutesContent() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="commandes" element={<Commandes />} />
      <Route path="commandes/:id" element={<RecordDetail endpoint="/commandes/" title="Commande" />} />
      <Route path="expeditions" element={<Expeditions />} />
      <Route path="expeditions/:id" element={<RecordDetail endpoint="/expeditions/" title="Expédition" />} />
      <Route path="transporteurs" element={<Transporteurs />} />
      <Route path="transporteurs/:id" element={<RecordDetail endpoint="/transporteurs/" title="Transporteur" />} />
      <Route path="entrepots" element={<Entrepots />} />
      <Route path="entrepots/:id" element={<RecordDetail endpoint="/entrepots/" title="Entrepôt" />} />
      <Route path="etl" element={<EtlRuns />} />
      <Route path="etl/runs/:id" element={<RecordDetail endpoint="/etl/runs/" title="Exécution ETL" />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return <Routes><Route path="/login" element={tokens.get() ? <Navigate to="/" replace /> : <Login />} /><Route element={<RequireAuth />}><Route path="/*" element={<Shell />} /></Route></Routes>;
}
