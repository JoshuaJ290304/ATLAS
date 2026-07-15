import Icon from "./Icon";

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <main className="relative grid min-h-screen overflow-hidden bg-slate-950 lg:grid-cols-[1.12fr_.88fr]">
      <div className="pointer-events-none absolute -left-40 -top-40 h-96 w-96 rounded-full bg-indigo-500/30 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-1/3 h-80 w-80 rounded-full bg-cyan-400/15 blur-3xl" />
      <section className="relative hidden flex-col justify-between p-12 text-white lg:flex xl:p-16">
        <div className="flex items-center gap-3">
          <span className="atlas-brand-mark"><Icon name="atlas" className="h-6 w-6" /></span>
          <div><p className="text-xl font-black">ATLAS</p><p className="text-xs text-indigo-200">AI-assisted software engineering</p></div>
        </div>
        <div className="max-w-2xl">
          <p className="mb-5 text-xs font-black uppercase tracking-[.3em] text-cyan-200">From requirements to reliable change</p>
          <h1 className="text-5xl font-black leading-[1.05] tracking-[-.045em] xl:text-6xl">
            Understand every requirement, link, and impact.
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-8 text-indigo-100">
            Extract project knowledge, build evidence-backed traceability, assess change risk, and ask grounded questions from one polished workspace.
          </p>
          <div className="mt-9 grid max-w-xl grid-cols-3 gap-3">
            {[["shield","Secure"],["trace","Traceable"],["assistant","AI grounded"]].map(([icon,label]) => (
              <div key={label} className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm">
                <Icon name={icon} className="h-5 w-5 text-cyan-200" />
                <p className="mt-3 text-sm font-extrabold">{label}</p>
              </div>
            ))}
          </div>
        </div>
        <p className="text-sm text-indigo-200">MCA Major Project · Version 0.7.0</p>
      </section>

      <section className="relative grid place-items-center bg-slate-50/95 px-5 py-12 backdrop-blur-xl">
        <div className="w-full max-w-md rounded-[28px] border border-white bg-white/95 p-7 shadow-2xl shadow-indigo-950/15 sm:p-9">
          <div className="mb-7 flex items-center gap-3 lg:hidden">
            <span className="atlas-brand-mark"><Icon name="atlas" className="h-6 w-6" /></span>
            <p className="text-xl font-black text-slate-900">ATLAS</p>
          </div>
          <p className="atlas-eyebrow">Secure workspace</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-slate-950">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </section>
    </main>
  );
}
