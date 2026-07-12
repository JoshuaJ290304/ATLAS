export default function AuthLayout({ title, subtitle, children }) {
  return (
    <main className="grid min-h-screen bg-slate-950 lg:grid-cols-2">
      <section className="hidden flex-col justify-between bg-gradient-to-br from-indigo-700 via-violet-700 to-slate-950 p-12 text-white lg:flex">
        <div className="text-2xl font-black tracking-tight">ATLAS</div>
        <div className="max-w-xl">
          <p className="mb-4 text-sm font-bold uppercase tracking-[0.28em] text-indigo-200">
            Software engineering intelligence
          </p>
          <h1 className="text-5xl font-black leading-tight">
            Connect requirements to every artifact they influence.
          </h1>
          <p className="mt-6 text-lg leading-8 text-indigo-100">
            Build traceability, assess change impact, and query project knowledge from one workspace.
          </p>
        </div>
        <p className="text-sm text-indigo-200">MCA Major Project - Milestone 1</p>
      </section>

      <section className="grid place-items-center bg-slate-50 px-5 py-12">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/50">
          <p className="mb-7 text-xl font-black text-indigo-700 lg:hidden">ATLAS</p>
          <h2 className="text-3xl font-black tracking-tight text-slate-900">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </section>
    </main>
  );
}
