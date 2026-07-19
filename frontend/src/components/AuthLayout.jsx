import { useEffect } from "react";

import { PRODUCT } from "../config/product";
import Icon from "./Icon";

export default function AuthLayout({ title, subtitle, children }) {
  useEffect(() => {
    document.title = `${title} · ${PRODUCT.name}`;
  }, [title]);

  return (
    <main className="atlas-auth-shell">
      <div className="pointer-events-none absolute -left-40 -top-40 h-96 w-96 rounded-full bg-indigo-500/30 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-1/3 h-80 w-80 rounded-full bg-cyan-400/15 blur-3xl" />

      <section className="atlas-auth-hero" aria-label="ATLAS platform overview">
        <div className="flex items-center gap-3">
          <span className="atlas-brand-mark"><Icon name="atlas" className="h-6 w-6" /></span>
          <div>
            <p className="text-xl font-black">{PRODUCT.name}</p>
            <p className="text-xs text-indigo-200">{PRODUCT.tagline}</p>
          </div>
        </div>

        <div className="max-w-2xl">
          <p className="mb-5 text-xs font-black uppercase tracking-[.3em] text-cyan-200">From requirements to reliable change</p>
          <h1 className="text-5xl font-black leading-[1.05] tracking-[-.045em] xl:text-6xl">
            Understand every requirement, link, and impact.
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-8 text-indigo-100">
            Extract project knowledge, build evidence-backed traceability, assess change risk, and ask grounded questions from one secure workspace.
          </p>
          <div className="mt-9 grid max-w-xl grid-cols-3 gap-3">
            {[["shield", "Secure"], ["trace", "Traceable"], ["assistant", "Source grounded"]].map(([icon, label]) => (
              <div key={label} className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm">
                <Icon name={icon} className="h-5 w-5 text-cyan-200" />
                <p className="mt-3 text-sm font-extrabold">{label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="text-sm text-indigo-200">
          <p>{PRODUCT.description}</p>
          <p className="mt-1 text-xs text-indigo-300">Version {PRODUCT.version}</p>
        </div>
      </section>

      <section className="atlas-auth-form-area">
        <div className="atlas-auth-card">
          <div className="mb-7 flex items-center gap-3 lg:hidden">
            <span className="atlas-brand-mark"><Icon name="atlas" className="h-6 w-6" /></span>
            <div>
              <p className="text-xl font-black text-slate-900">{PRODUCT.name}</p>
              <p className="text-xs font-semibold text-slate-500">{PRODUCT.tagline}</p>
            </div>
          </div>
          <p className="atlas-eyebrow">Secure workspace</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-slate-950">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
        <footer className="atlas-auth-footer">
          <strong>Developed by {PRODUCT.developer}</strong>
          <span aria-hidden="true"> · </span>
          <span>© {PRODUCT.copyrightYear} {PRODUCT.name}</span>
          <span aria-hidden="true"> · </span>
          <span>Version {PRODUCT.version}</span>
        </footer>
      </section>
    </main>
  );
}

