import { useQueryClient } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { tokens } from "@/api/client";

const LIENS = [
  { to: "/", label: "Tableau de bord" },
  { to: "/anomalies", label: "Anomalies" },
  { to: "/commandes", label: "Commandes" },
];

export default function Layout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  function seDeconnecter() {
    tokens.clear();
    queryClient.clear();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <nav className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
          <span className="font-semibold text-slate-900">Chaîne logistique</span>
          {LIENS.map((lien) => (
            <NavLink
              key={lien.to}
              to={lien.to}
              end
              className={({ isActive }) =>
                isActive ? "font-medium text-slate-900" : "text-slate-500 hover:text-slate-900"
              }
            >
              {lien.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={seDeconnecter}
            className="ml-auto text-sm text-slate-500 hover:text-slate-900"
          >
            Se déconnecter
          </button>
        </nav>
      </header>
      <main className="mx-auto max-w-7xl p-4">
        <Outlet />
      </main>
    </div>
  );
}