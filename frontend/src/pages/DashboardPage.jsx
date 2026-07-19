import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import Icon from "../components/Icon";
import { Alert, EmptyState, FieldError, LoadingState, PageHeader, StatCard } from "../components/UI";
import { apiErrorMessage, clean, validateRequired } from "../utils/validation";

const PROJECT_ACTIONS = [
  { key: "documents", label: "Documents", caption: "Upload & extract", icon: "document", iconClass: "text-indigo-600", cardClass: "hover:border-indigo-200 hover:bg-indigo-50" },
  { key: "requirements", label: "Requirements", caption: "Classify & review", icon: "requirement", iconClass: "text-violet-600", cardClass: "hover:border-violet-200 hover:bg-violet-50" },
  { key: "traceability", label: "Traceability", caption: "Link artifacts", icon: "trace", iconClass: "text-emerald-600", cardClass: "hover:border-emerald-200 hover:bg-emerald-50" },
  { key: "governance", label: "Reviews", caption: "Approve & baseline", icon: "governance", iconClass: "text-sky-600", cardClass: "hover:border-sky-200 hover:bg-sky-50" },
  { key: "impact", label: "Impact", caption: "Assess change risk", icon: "impact", iconClass: "text-amber-600", cardClass: "hover:border-amber-200 hover:bg-amber-50" },
  { key: "assistant", label: "AI Assistant", caption: "Ask with sources", icon: "assistant", iconClass: "text-cyan-600", cardClass: "hover:border-cyan-200 hover:bg-cyan-50" },
  { key: "analytics", label: "Analytics", caption: "Health & reports", icon: "analytics", iconClass: "text-rose-600", cardClass: "hover:border-rose-200 hover:bg-rose-50" },
];

export default function DashboardPage() {
  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState({ name: "", description: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  async function loadProjects() {
    setLoading(true);
    try {
      const response = await api.get("/projects");
      setProjects(response.data);
      setError("");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load projects."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadProjects(); }, []);

  const filteredProjects = useMemo(() => {
    const normalized = clean(query).toLowerCase();
    if (!normalized) return projects;
    return projects.filter((project) =>
      `${project.name} ${project.description || ""}`.toLowerCase().includes(normalized),
    );
  }, [projects, query]);

  function validateProject() {
    const next = {
      name: validateRequired(form.name, "Project name", 2, 160),
      description:
        form.description.length > 4000 ? "Description must be at most 4000 characters." : "",
    };
    Object.keys(next).forEach((key) => !next[key] && delete next[key]);
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  }

  async function createProject(event) {
    event.preventDefault();
    if (!validateProject()) return;
    setCreating(true);
    setError("");
    setNotice("");
    try {
      const response = await api.post("/projects", {
        name: clean(form.name),
        description: clean(form.description) || null,
      });
      setProjects((current) => [response.data, ...current]);
      setForm({ name: "", description: "" });
      setFieldErrors({});
      setNotice(`Project “${response.data.name}” created successfully.`);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not create project."));
    } finally {
      setCreating(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Project command centre"
        title="Turn software requirements into connected engineering knowledge."
        description="Manage project evidence from source documents through requirement quality, traceability, governance, impact analysis, grounded AI answers, and executive analytics."
      >
        <div className="atlas-dashboard-summary" aria-label="Platform summary">
          <StatCard label="Projects" value={projects.length} detail="Owned workspaces" icon="home" tone="indigo" />
          <StatCard label="Platform" value="0.8.0" detail="Current release" icon="analytics" tone="violet" />
          <StatCard label="Capabilities" value="07" detail="Connected workflows" icon="trace" tone="emerald" />
          <StatCard label="Security" value="Protected" detail="Client and API validation" icon="shield" tone="cyan" />
        </div>
      </PageHeader>

      {(error || notice) && (
        <div className="mt-6 space-y-3">
          {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}
          {notice && <Alert type="success" onClose={() => setNotice("")}>{notice}</Alert>}
        </div>
      )}

      <section className="mt-8 grid gap-7 xl:grid-cols-[360px_minmax(0,1fr)]">
        <form onSubmit={createProject} noValidate className="atlas-panel h-fit xl:sticky xl:top-24">
          <div className="flex items-start gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-indigo-50 text-indigo-600"><Icon name="plus" /></span>
            <div><h2 className="text-xl font-black text-slate-950">Create project</h2><p className="mt-1 text-sm leading-6 text-slate-500">Start with a clear project identity. All evidence remains isolated inside it.</p></div>
          </div>
          <label className="atlas-label mt-6">
            Project name
            <input
              value={form.name}
              aria-invalid={Boolean(fieldErrors.name)}
              onChange={(event) => {
                setForm({ ...form, name: event.target.value });
                if (fieldErrors.name) setFieldErrors({ ...fieldErrors, name: "" });
              }}
              className="atlas-input"
              placeholder="Finance Management System"
              maxLength={160}
            />
            <div className="flex justify-between"><FieldError>{fieldErrors.name}</FieldError><span className="atlas-help ml-auto">{form.name.length}/160</span></div>
          </label>
          <label className="atlas-label mt-5">
            Description <span className="font-normal text-slate-400">(optional)</span>
            <textarea
              rows={5}
              value={form.description}
              aria-invalid={Boolean(fieldErrors.description)}
              onChange={(event) => {
                setForm({ ...form, description: event.target.value });
                if (fieldErrors.description) setFieldErrors({ ...fieldErrors, description: "" });
              }}
              className="atlas-textarea"
              placeholder="Describe the business goal, users, and main system boundary."
              maxLength={4000}
            />
            <div className="flex justify-between"><FieldError>{fieldErrors.description}</FieldError><span className="atlas-help ml-auto">{form.description.length}/4000</span></div>
          </label>
          <button type="submit" disabled={creating} className="atlas-button-primary mt-5 w-full">
            <Icon name="plus" className="h-4 w-4" /> {creating ? "Creating project..." : "Create project"}
          </button>
        </form>

        <div className="min-w-0">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div><h2 className="text-2xl font-black tracking-tight text-slate-950">Your projects</h2><p className="mt-1 text-sm text-slate-500">Open a module or review project health.</p></div>
            <div className="flex gap-2">
              <label className="relative flex-1 sm:w-64">
                <Icon name="search" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input value={query} onChange={(event) => setQuery(event.target.value)} className="atlas-input !mt-0 !pl-10" placeholder="Search projects" aria-label="Search projects" />
              </label>
              <button type="button" onClick={loadProjects} className="atlas-button-secondary" aria-label="Refresh projects"><Icon name="refresh" className="h-4 w-4" /></button>
            </div>
          </div>

          {loading ? (
            <LoadingState label="Loading projects..." />
          ) : projects.length === 0 ? (
            <div className="mt-5"><EmptyState icon="home" title="No projects yet" description="Create the first ATLAS workspace using the form." /></div>
          ) : filteredProjects.length === 0 ? (
            <div className="mt-5"><EmptyState icon="search" title="No matching projects" description="Try a different project name or clear the search." /></div>
          ) : (
            <div className="mt-5 grid gap-5 2xl:grid-cols-2">
              {filteredProjects.map((project) => (
                <article key={project.id} className="atlas-card flex min-w-0 flex-col overflow-hidden">
                  <div className="h-1.5 bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-500" />
                  <div className="flex flex-1 flex-col p-6">
                    <div className="flex min-w-0 items-start justify-between gap-4">
                      <div className="min-w-0"><p className="text-xs font-black uppercase tracking-[.15em] text-indigo-500">Software project</p><h3 className="mt-2 break-words text-xl font-black text-slate-950">{project.name}</h3></div>
                      <span className="shrink-0 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-black capitalize text-emerald-700">{project.status}</span>
                    </div>
                    <p className="mt-3 min-h-12 flex-1 break-words text-sm leading-6 text-slate-600">{project.description || "No project description has been added yet."}</p>
                    <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-400"><Icon name="clock" className="h-4 w-4" />Created {new Date(project.created_at).toLocaleDateString()}</div>
                    <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
                      {PROJECT_ACTIONS.map((action) => (
                        <Link key={action.key} to={`/projects/${project.id}/${action.key}`} className={`group rounded-xl border border-slate-200 p-3 no-underline transition hover:-translate-y-0.5 ${action.cardClass}`}>
                          <div className="flex items-center gap-2"><Icon name={action.icon} className={`h-4 w-4 ${action.iconClass}`} /><span className="text-xs font-black text-slate-800">{action.label}</span></div>
                          <p className="mt-1 text-[10px] text-slate-400">{action.caption}</p>
                        </Link>
                      ))}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </AppShell>
  );
}
