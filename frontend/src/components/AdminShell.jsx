import { Link, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { PRODUCT } from "../config/product";
import Icon from "./Icon";

const items = [
  { to: "/admin", label: "Overview", icon: "analytics" },
  { to: "/admin/users", label: "Users", icon: "users" },
  { to: "/admin/projects", label: "Projects", icon: "home" },
  { to: "/admin/audit", label: "Audit log", icon: "history" },
  { to: "/admin/system", label: "System health", icon: "server" },
  { to: "/admin/settings", label: "Platform settings", icon: "settings" },
];

export default function AdminShell({ title, description, children, actions }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const initial = (user?.name || "A").trim().charAt(0).toUpperCase();

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <Link to="/admin" className="admin-brand">
          <span className="atlas-brand-mark"><Icon name="atlas" className="h-6 w-6" /></span>
          <span><strong>{PRODUCT.name}</strong><small>Platform administration</small></span>
        </Link>
        <nav className="admin-nav" aria-label="Administration">
          {items.map((item) => {
            const active = item.to === "/admin" ? location.pathname === item.to : location.pathname.startsWith(item.to);
            return (
              <Link key={item.to} to={item.to} className={active ? "is-active" : ""}>
                <Icon name={item.icon} className="h-5 w-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="admin-sidebar-footer">
          <Link to="/" className="atlas-button-secondary w-full"><Icon name="arrowLeft" className="h-4 w-4" />Return to ATLAS</Link>
          <button type="button" onClick={logout} className="atlas-button-secondary w-full"><Icon name="logout" className="h-4 w-4" />Log out</button>
        </div>
      </aside>

      <div className="admin-workspace">
        <header className="admin-topbar">
          <div className="min-w-0">
            <p className="atlas-eyebrow">Administration & platform operations</p>
            <h1>{title}</h1>
            {description && <p>{description}</p>}
          </div>
          <div className="admin-topbar-actions">
            {actions}
            <div className="atlas-account-copy"><p>{user?.name}</p><span>{user?.email}</span></div>
            <div className="atlas-avatar" aria-hidden="true">{initial}</div>
          </div>
        </header>
        <main className="admin-main">{children}</main>
        <footer className="admin-footer">{PRODUCT.name} {PRODUCT.version} · Administrative actions are recorded in the platform audit log.</footer>
      </div>
    </div>
  );
}
