import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";

export default function DashboardPage() {
  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState({ name: "", description: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  async function loadProjects() {
    try {
      const response = await api.get("/projects");
      setProjects(response.data);
      setError("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not load projects.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  async function createProject(event) {
    event.preventDefault();
    setCreating(true);
    setError("");
    try {
      const response = await api.post("/projects", form);
      setProjects((current) => [response.data, ...current]);
      setForm({ name: "", description: "" });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not create project.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <AppShell>
      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-indigo-600">
            Project workspace
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            Build traceability from the requirement outward.
          </h1>
          <p className="mt-4 max-w-3xl leading-7 text-slate-600">
            Milestones 1–3 provide secure projects, document processing, and a reviewable requirement
            register. Traceability graphs, impact analysis, and the AI assistant will attach to these records.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Metric label="Projects" value={projects.length} />
          <Metric label="Current milestone" value="03" />
          <Metric label="Requirements" value="Ready" />
          <Metric label="Coverage" value="-" />
        </div>
      </section>

      <section className="mt-10 grid gap-8 lg:grid-cols-[380px_1fr]">
        <form onSubmit={createProject} className="h-fit rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-black text-slate-900">Create project</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Each uploaded SRS and all derived artifacts will belong to one project.
          </p>
          <label className="mt-5 block text-sm font-semibold text-slate-700">
            Project name
            <input
              required
              minLength={2}
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
              placeholder="Finance Management System"
            />
          </label>
          <label className="mt-5 block text-sm font-semibold text-slate-700">
            Description
            <textarea
              rows={4}
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              className="mt-2 w-full resize-none rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
              placeholder="Describe the project and its main goal."
            />
          </label>
          {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button
            disabled={creating}
            className="mt-5 w-full rounded-xl bg-indigo-600 px-4 py-3 font-bold text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {creating ? "Creating..." : "Create project"}
          </button>
        </form>

        <div>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-black text-slate-900">Your projects</h2>
            <button onClick={loadProjects} className="text-sm font-bold text-indigo-700 hover:underline">
              Refresh
            </button>
          </div>

          {loading ? (
            <p className="mt-5 text-slate-500">Loading projects...</p>
          ) : projects.length === 0 ? (
            <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <p className="font-bold text-slate-800">No projects yet</p>
              <p className="mt-2 text-sm text-slate-500">Create the first project using the form.</p>
            </div>
          ) : (
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {projects.map((project) => (
                <article key={project.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex items-start justify-between gap-4">
                    <h3 className="text-lg font-black text-slate-900">{project.name}</h3>
                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold capitalize text-emerald-700">
                      {project.status}
                    </span>
                  </div>
                  <p className="mt-3 min-h-12 text-sm leading-6 text-slate-600">
                    {project.description || "No description provided."}
                  </p>
                  <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
                    <span className="text-xs text-slate-500">
                      Created {new Date(project.created_at).toLocaleString()}
                    </span>
                    <div className="flex gap-2">
                      <Link
                        to={`/projects/${project.id}/documents`}
                        className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-bold text-slate-700 hover:bg-slate-200"
                      >
                        Documents
                      </Link>
                      <Link
                        to={`/projects/${project.id}/requirements`}
                        className="rounded-lg bg-indigo-50 px-3 py-2 text-sm font-bold text-indigo-700 hover:bg-indigo-100"
                      >
                        Requirements
                      </Link>
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

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-slate-900">{value}</p>
    </div>
  );
}
