import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";

import { PRODUCT } from "../config/product";
import { useAuth } from "../context/AuthContext";
import Icon from "./Icon";

const PAGE_TITLES = {
  documents: "Documents",
  requirements: "Requirements",
  traceability: "Traceability",
  governance: "Reviews & Baselines",
  impact: "Impact Analysis",
  assistant: "AI Assistant",
  analytics: "Analytics",
  releases: "Release Readiness",
  "test-cases": "Test Cases",
};

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const initial = (user?.name || "A").trim().charAt(0).toUpperCase();

  useEffect(() => {
    const segment = location.pathname.split("/").filter(Boolean).at(-1);
    const page = location.pathname === "/" ? "Projects" : PAGE_TITLES[segment] || "Workspace";
    document.title = `${page} · ${PRODUCT.name}`;
  }, [location.pathname]);

  return (
    <div className="atlas-shell">
      <a className="atlas-skip-link" href="#atlas-main-content">Skip to main content</a>
      <header className="atlas-topbar">
        <div className="atlas-topbar-inner">
          <Link to="/" className="atlas-brand" aria-label={`${PRODUCT.name} dashboard`}>
            <span className="atlas-brand-mark"><Icon name="atlas" className="h-6 w-6" strokeWidth={1.6} /></span>
            <span className="min-w-0">
              <strong className="atlas-brand-name">{PRODUCT.name}</strong>
              <span className="atlas-brand-tagline">{PRODUCT.tagline}</span>
            </span>
          </Link>

          <div className="atlas-account-area">
            <div className="atlas-system-status" title="Authenticated workspace">
              <span aria-hidden="true" />
              <span>Protected session</span>
            </div>
            <div className="atlas-account-copy">
              <p>{user?.name}</p>
              <span>{user?.email}</span>
            </div>
            <div className="atlas-avatar" aria-hidden="true">{initial}</div>
            <button type="button" onClick={logout} className="atlas-button-secondary">
              <Icon name="logout" className="h-4 w-4" />
              <span className="hidden sm:inline">Log out</span>
              <span className="sm:hidden">Exit</span>
            </button>
          </div>
        </div>
      </header>

      <main id="atlas-main-content" className="atlas-main" tabIndex="-1">{children}</main>

      <footer className="atlas-footer">
        <div className="atlas-footer-inner">
          <div>
            <p className="atlas-footer-brand">{PRODUCT.name}</p>
            <p>{PRODUCT.description}</p>
          </div>
          <div className="atlas-footer-meta">
            <span className="atlas-footer-developer">Developed by {PRODUCT.developer}</span>
            <span aria-hidden="true">•</span>
            <span>Version {PRODUCT.version}</span>
            <span aria-hidden="true">•</span>
            <span>Secure project workspace</span>
            <span aria-hidden="true">•</span>
            <span>© {PRODUCT.copyrightYear} {PRODUCT.name}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
