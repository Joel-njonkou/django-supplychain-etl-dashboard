import { Navigate, Outlet } from "react-router-dom";

import { tokens } from "@/api/client";

export default function RequireAuth() {
  if (!tokens.getAccess()) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}