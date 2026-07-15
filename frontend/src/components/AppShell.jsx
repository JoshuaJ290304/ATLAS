import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import Icon from "./Icon";

export default function AppShell({ children }) {
  const { user, logout } = useAuth();

  return (
    <div className="atlas-shell">
      <header className="atlas-topbar">
        <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-4 py-3 sm:px-5">
          <Link to="/" className="flex min-w-0 items-center gap-3 text-slate-900 no-underline">
            <span className="atlas-brand-mark"><Icon name="atlas" className="h-6 w-6" strokeWidth={1.6} /></span>
            <span className="min-w-0">
              <strong className="block text-lg font-black tracking-tight">ATLAS</strong>
              <span className="hidden text-[11px] font-semibold text-slate-500 sm:block">Engineering intelligence workspace</span>
            </span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden text-right md:block">
              <p className="text-sm font-extrabold text-slate-800">{user?.name}</p>
              <p className="text-xs text-slate-500">{user?.email}</p>
            </div>
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 text-sm font-black text-indigo-700">
              {(user?.name || "A").trim().charAt(0).toUpperCase()}
            </div>
            <button type="button" onClick={logout} className="atlas-button-secondary">
              <span className="hidden sm:inline">Log out</span>
              <span className="sm:hidden">Exit</span>
            </button>
          </div>
        </div>
      </header>
      <main className="atlas-main">{children}</main>
      <footer className="border-t border-slate-200/80 bg-white/60 py-5 text-center text-xs text-slate-400">
        ATLAS v0.7.0 · Requirement traceability and change intelligence
      </footer>
    </div>
  );
}
