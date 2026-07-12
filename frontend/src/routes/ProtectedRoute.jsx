import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="grid min-h-screen place-items-center text-slate-600">Loading ATLAS...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}
