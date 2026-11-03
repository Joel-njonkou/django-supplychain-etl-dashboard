import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "@/components/Layout";
import RequireAuth from "@/components/RequireAuth";
import Anomalies from "@/pages/Anomalies";
import Commandes from "@/pages/Commandes";
import Dashboard from "@/pages/Dashboard";
import Login from "@/pages/Login";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/anomalies" element={<Anomalies />} />
          <Route path="/commandes" element={<Commandes />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}