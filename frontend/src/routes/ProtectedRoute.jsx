import { Navigate } from "react-router-dom";

import Icon from "../components/Icon";
import { PRODUCT } from "../config/product";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="atlas-route-loading" role="status" aria-live="polite">
        <span className="atlas-brand-mark"><Icon name="atlas" className="h-6 w-6" /></span>
        <div>
          <p>{PRODUCT.name}</p>
          <span>Preparing your workspace…</span>
        </div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}
