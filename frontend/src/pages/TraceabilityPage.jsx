import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import ProjectNav from "../components/ProjectNav";
import { FieldError } from "../components/UI";
import { apiErrorMessage, clean, validateRequired } from "../utils/validation";

const EMPTY_ARTIFACT = {
  name: "",
  artifact_type: "api",
  description: "",
  technical_notes: "",
};

const EMPTY_MANUAL_LINK = {
  requirement_id: "",
  artifact_id: "",
  link_type: "",
  evidence_note: "",
};

const TYPE_LABELS = {
  api: "API",
  database_table: "Database table",
  test_case: "Test case",
  uml_component: "UML component",
};

const LINK_TYPE_LABELS = {
  implements: "Implements",
  stores: "Stores data for",
  verifies: "Verifies",
  represents: "Represents",
  relates_to: "Relates to",
};

function emptySummary() {
  return {
    requirement_total: 0,
    linked_requirements: 0,
    uncovered_requirements: 0,
    requirement_coverage_percent: 0,
    artifact_total: 0,
    linked_artifacts: 0,
    uncovered_artifacts: 0,
    artifact_coverage_percent: 0,
    suggested_links: 0,
    accepted_links: 0,
    rejected_links: 0,
    uncovered_requirement_codes: [],
    uncovered_artifact_codes: [],
  };
}

export default function TraceabilityPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [requirements, setRequirements] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [links, setLinks] = useState([]);
  const [summary, setSummary] = useState(emptySummary());
  const [matrix, setMatrix] = useState({ requirements: [], artifacts: [], cells: [] });
  const [artifactForm, setArtifactForm] = useState(EMPTY_ARTIFACT);
  const [manualLink, setManualLink] = useState(EMPTY_MANUAL_LINK);
  const [editingArtifactId, setEditingArtifactId] = useState(null);
  const [editArtifactForm, setEditArtifactForm] = useState(null);
  const [artifactErrors, setArtifactErrors] = useState({});
  const [editArtifactErrors, setEditArtifactErrors] = useState({});
  const [manualLinkErrors, setManualLinkErrors] = useState({});
  const [minimumConfidence, setMinimumConfidence] = useState(0.3);
  const [replaceSuggestions, setReplaceSuggestions] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadWorkspace() {
    setLoading(true);
    setError("");
    try {
      const [
        projectResponse,
        requirementsResponse,
        artifactsResponse,
        linksResponse,
        summaryResponse,
        matrixResponse,
      ] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/requirements`),
        api.get(`/projects/${projectId}/artifacts`),
        api.get(`/projects/${projectId}/trace-links`),
        api.get(`/projects/${projectId}/traceability/summary`),
        api.get(`/projects/${projectId}/traceability/matrix`),
      ]);
      setProject(projectResponse.data);
      setRequirements(requirementsResponse.data);
      setArtifacts(artifactsResponse.data);
      setLinks(linksResponse.data);
      setSummary(summaryResponse.data);
      setMatrix(matrixResponse.data);

      setManualLink((current) => ({
        ...current,
        requirement_id: current.requirement_id || requirementsResponse.data[0]?.id || "",
        artifact_id: current.artifact_id || artifactsResponse.data[0]?.id || "",
      }));
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not load traceability data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkspace();
  }, [projectId]);

  const requirementById = useMemo(
    () => Object.fromEntries(requirements.map((item) => [item.id, item])),
    [requirements],
  );
  const artifactById = useMemo(
    () => Object.fromEntries(artifacts.map((item) => [item.id, item])),
    [artifacts],
  );
  const matrixCellByPair = useMemo(
    () =>
      Object.fromEntries(
        matrix.cells.map((cell) => [`${cell.requirement_id}:${cell.artifact_id}`, cell]),
      ),
    [matrix],
  );


  function validateArtifact(values) {
    const next = {
      name: validateRequired(values.name, "Artifact name", 2, 180),
      description: validateRequired(values.description, "Artifact description", 5, 10000),
      technical_notes:
        values.technical_notes.length > 4000 ? "Technical notes must be at most 4000 characters." : "",
    };
    Object.keys(next).forEach((key) => !next[key] && delete next[key]);
    return next;
  }

  async function createArtifact(event) {
    event.preventDefault();
    const validationErrors = validateArtifact(artifactForm);
    setArtifactErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      await api.post(`/projects/${projectId}/artifacts`, {
        name: clean(artifactForm.name),
        artifact_type: artifactForm.artifact_type,
        description: clean(artifactForm.description),
        technical_details: clean(artifactForm.technical_notes)
          ? { notes: clean(artifactForm.technical_notes) }
          : {},
      });
      setArtifactForm(EMPTY_ARTIFACT);
      setArtifactErrors({});
      setNotice("Software artifact created.");
      await loadWorkspace();
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not create the artifact."));
    } finally {
      setSaving(false);
    }
  }

  function beginArtifactEdit(artifact) {
    setEditingArtifactId(artifact.id);
    setEditArtifactForm({
      name: artifact.name,
      artifact_type: artifact.artifact_type,
      description: artifact.description,
      technical_notes: artifact.technical_details?.notes || "",
    });
    setError("");
    setNotice("");
    setEditArtifactErrors({});
  }

  async function saveArtifact(event, artifactId) {
    event.preventDefault();
    const validationErrors = validateArtifact(editArtifactForm);
    setEditArtifactErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;
    setSaving(true);
    setError("");
    try {
      await api.patch(`/projects/${projectId}/artifacts/${artifactId}`, {
        name: clean(editArtifactForm.name),
        artifact_type: editArtifactForm.artifact_type,
        description: clean(editArtifactForm.description),
        technical_details: clean(editArtifactForm.technical_notes)
          ? { notes: clean(editArtifactForm.technical_notes) }
          : {},
      });
      setEditingArtifactId(null);
      setEditArtifactForm(null);
      setEditArtifactErrors({});
      setNotice("Artifact updated. Regenerate suggestions if its meaning changed.");
      await loadWorkspace();
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not update the artifact."));
    } finally {
      setSaving(false);
    }
  }

  async function deleteArtifact(artifact) {
    const confirmed = window.confirm(
      `Delete ${artifact.code}: ${artifact.name}? Its trace links will also be deleted.`,
    );
    if (!confirmed) return;
    setError("");
    try {
      await api.delete(`/projects/${projectId}/artifacts/${artifact.id}`);
      setNotice(`${artifact.code} deleted.`);
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not delete the artifact.");
    }
  }

  async function generateSuggestions(event) {
    event.preventDefault();
    setSuggesting(true);
    setError("");
    setNotice("");
    try {
      const response = await api.post(`/projects/${projectId}/trace-links/suggest`, {
        minimum_confidence: Number(minimumConfidence),
        replace_system_suggestions: replaceSuggestions,
      });
      setNotice(
        `Evaluated ${response.data.evaluated_pairs} pair(s); created ` +
          `${response.data.created_count} suggestion(s); skipped ` +
          `${response.data.skipped_existing_count} existing pair(s).`,
      );
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not generate suggestions.");
    } finally {
      setSuggesting(false);
    }
  }

  async function createManualTrace(event) {
    event.preventDefault();
    const validationErrors = {
      requirement_id: manualLink.requirement_id ? "" : "Select a requirement.",
      artifact_id: manualLink.artifact_id ? "" : "Select an artifact.",
      evidence_note:
        manualLink.evidence_note.length > 1000 ? "Evidence must be at most 1000 characters." : "",
    };
    Object.keys(validationErrors).forEach((key) => !validationErrors[key] && delete validationErrors[key]);
    setManualLinkErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      await api.post(`/projects/${projectId}/trace-links`, {
        requirement_id: manualLink.requirement_id,
        artifact_id: manualLink.artifact_id,
        link_type: manualLink.link_type || null,
        confidence_score: 1,
        evidence_note: clean(manualLink.evidence_note) || null,
      });
      setManualLink((current) => ({ ...current, evidence_note: "", link_type: "" }));
      setManualLinkErrors({});
      setNotice("Manual trace link accepted and added to coverage.");
      await loadWorkspace();
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not create the trace link."));
    } finally {
      setSaving(false);
    }
  }

  async function updateLink(traceLinkId, status) {
    setError("");
    try {
      await api.patch(`/projects/${projectId}/trace-links/${traceLinkId}`, { status });
      setNotice(`Trace link marked ${status}.`);
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not update the trace link.");
    }
  }

  async function deleteLink(traceLinkId) {
    const confirmed = window.confirm("Delete this trace link?");
    if (!confirmed) return;
    setError("");
    try {
      await api.delete(`/projects/${projectId}/trace-links/${traceLinkId}`);
      setNotice("Trace link deleted.");
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not delete the trace link.");
    }
  }

  return (
    <AppShell>
      <ProjectNav projectId={projectId} />

      <section className="atlas-page-header">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-indigo-600">
            Milestone 4
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            {project?.name || "Traceability engine"}
          </h1>
          <p className="mt-4 max-w-3xl leading-7 text-slate-600">
            Register software artifacts, review explainable requirement links, and measure coverage
            using only accepted evidence.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
          <Metric label="Requirement coverage" value={`${summary.requirement_coverage_percent}%`} />
          <Metric label="Artifact coverage" value={`${summary.artifact_coverage_percent}%`} />
          <Metric label="Accepted links" value={summary.accepted_links} />
          <Metric label="To review" value={summary.suggested_links} />
          <Metric label="Rejected links" value={summary.rejected_links} />
        </div>
      </section>

      {(error || notice) && (
        <section className="mt-6 space-y-3">
          {error && <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
          {notice && (
            <p className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{notice}</p>
          )}
        </section>
      )}

      <section className="mt-10 grid gap-8 xl:grid-cols-[380px_1fr]">
        <div className="space-y-6">
          <form
            onSubmit={createArtifact}
            noValidate
            className="atlas-panel"
          >
            <h2 className="text-xl font-black text-slate-900">Add software artifact</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Add the APIs, tables, tests, and UML components affected by requirements.
            </p>
            <ArtifactFields form={artifactForm} setForm={setArtifactForm} errors={artifactErrors} clearErrors={setArtifactErrors} />
            <button
              disabled={saving}
              className="mt-5 w-full rounded-xl bg-indigo-600 px-4 py-3 font-bold text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {saving ? "Saving..." : "Create artifact"}
            </button>
          </form>

          <form
            onSubmit={generateSuggestions}
            className="atlas-panel"
          >
            <h2 className="text-xl font-black text-slate-900">Suggest trace links</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Scores are explainable and based on shared terms, artifact names, and type cues.
            </p>
            <label className="mt-5 block text-sm font-semibold text-slate-700">
              Minimum confidence: {Number(minimumConfidence).toFixed(2)}
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={minimumConfidence}
                onChange={(event) => setMinimumConfidence(event.target.value)}
                className="mt-3 w-full"
              />
            </label>
            <label className="mt-4 flex items-start gap-3 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={replaceSuggestions}
                onChange={(event) => setReplaceSuggestions(event.target.checked)}
                className="mt-1"
              />
              Replace unresolved system suggestions before recalculating
            </label>
            <button
              disabled={suggesting || requirements.length === 0 || artifacts.length === 0}
              className="mt-5 w-full rounded-xl bg-slate-900 px-4 py-3 font-bold text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {suggesting ? "Analyzing pairs..." : "Generate suggestions"}
            </button>
          </form>

          <form
            onSubmit={createManualTrace}
            noValidate
            className="atlas-panel"
          >
            <h2 className="text-xl font-black text-slate-900">Create manual link</h2>
            <SelectField
              label="Requirement"
              value={manualLink.requirement_id}
              onChange={(value) => setManualLink({ ...manualLink, requirement_id: value })}
              options={requirements.map((item) => ({
                value: item.id,
                label: `${item.code} — ${item.title}`,
              }))}
              error={manualLinkErrors.requirement_id}
            />
            <SelectField
              label="Artifact"
              value={manualLink.artifact_id}
              onChange={(value) => setManualLink({ ...manualLink, artifact_id: value })}
              options={artifacts.map((item) => ({
                value: item.id,
                label: `${item.code} — ${item.name}`,
              }))}
              error={manualLinkErrors.artifact_id}
            />
            <SelectField
              label="Link type (automatic when blank)"
              value={manualLink.link_type}
              onChange={(value) => setManualLink({ ...manualLink, link_type: value })}
              blankLabel="Infer from artifact type"
              options={Object.entries(LINK_TYPE_LABELS).map(([value, label]) => ({ value, label }))}
            />
            <label className="mt-4 block text-sm font-semibold text-slate-700">
              Evidence note
              <textarea
                rows={3}
                value={manualLink.evidence_note}
                onChange={(event) =>
                  setManualLink({ ...manualLink, evidence_note: event.target.value })
                }
                aria-invalid={Boolean(manualLinkErrors.evidence_note)}
                className="atlas-textarea"
                placeholder="Why does this artifact satisfy or verify the requirement?"
                maxLength={1000}
              />
              <FieldError>{manualLinkErrors.evidence_note}</FieldError>
            </label>
            <button
              disabled={saving || requirements.length === 0 || artifacts.length === 0}
              className="mt-5 w-full rounded-xl bg-emerald-600 px-4 py-3 font-bold text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Add accepted link
            </button>
          </form>
        </div>

        <div className="space-y-8">
          <section>
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black text-slate-900">Artifact register</h2>
                <p className="mt-1 text-sm text-slate-500">{artifacts.length} artifact(s)</p>
              </div>
              <button onClick={loadWorkspace} className="text-sm font-bold text-indigo-700 hover:underline">
                Refresh
              </button>
            </div>

            {loading ? (
              <p className="mt-5 text-slate-500">Loading traceability workspace...</p>
            ) : artifacts.length === 0 ? (
              <EmptyState text="Create the first API, database table, test case, or UML component." />
            ) : (
              <div className="mt-5 grid gap-4 lg:grid-cols-2">
                {artifacts.map((artifact) => (
                  <article
                    key={artifact.id}
                    className="atlas-card p-5"
                  >
                    {editingArtifactId === artifact.id ? (
                      <form onSubmit={(event) => saveArtifact(event, artifact.id)} noValidate>
                        <ArtifactFields form={editArtifactForm} setForm={setEditArtifactForm} errors={editArtifactErrors} clearErrors={setEditArtifactErrors} />
                        <div className="mt-4 flex gap-2">
                          <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white">
                            Save
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setEditingArtifactId(null);
                              setEditArtifactForm(null);
                            }}
                            className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-bold text-slate-700"
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : (
                      <>
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-xs font-black uppercase tracking-wider text-indigo-600">
                              {artifact.code}
                            </p>
                            <h3 className="mt-1 text-lg font-black text-slate-900">{artifact.name}</h3>
                          </div>
                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
                            {TYPE_LABELS[artifact.artifact_type]}
                          </span>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-slate-600">{artifact.description}</p>
                        {artifact.technical_details?.notes && (
                          <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-600">
                            {artifact.technical_details.notes}
                          </p>
                        )}
                        <div className="mt-4 flex gap-2 border-t border-slate-100 pt-4">
                          <button
                            onClick={() => beginArtifactEdit(artifact)}
                            className="rounded-lg bg-indigo-50 px-3 py-2 text-sm font-bold text-indigo-700"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => deleteArtifact(artifact)}
                            className="rounded-lg bg-red-50 px-3 py-2 text-sm font-bold text-red-700"
                          >
                            Delete
                          </button>
                        </div>
                      </>
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>

          <section>
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black text-slate-900">Link review queue</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Accept correct evidence, reject false matches, or delete obsolete links.
                </p>
              </div>
              <div className="flex gap-2 text-xs font-bold">
                <StatusPill status="suggested" count={summary.suggested_links} />
                <StatusPill status="accepted" count={summary.accepted_links} />
                <StatusPill status="rejected" count={summary.rejected_links} />
              </div>
            </div>

            {links.length === 0 ? (
              <EmptyState text="Generate suggestions or create a manual trace link." />
            ) : (
              <div className="mt-5 space-y-4">
                {links.map((link) => {
                  const requirement = requirementById[link.requirement_id];
                  const artifact = artifactById[link.artifact_id];
                  return (
                    <article
                      key={link.id}
                      className="atlas-card p-5"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <StatusBadge status={link.status} />
                            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                              {link.source}
                            </span>
                            <span className="text-xs font-bold text-slate-500">
                              Confidence {(link.confidence_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="mt-3 font-bold text-slate-900">
                            {requirement?.code || "Requirement"}: {requirement?.title || "Deleted"}
                          </p>
                          <p className="mt-1 text-sm text-slate-600">
                            {LINK_TYPE_LABELS[link.link_type]} → {artifact?.code || "Artifact"}: {artifact?.name || "Deleted"}
                          </p>
                          {link.evidence?.rationale && (
                            <p className="mt-3 rounded-lg bg-indigo-50 p-3 text-xs leading-5 text-indigo-800">
                              {link.evidence.rationale}
                            </p>
                          )}
                          {link.evidence?.note && (
                            <p className="mt-3 rounded-lg bg-emerald-50 p-3 text-xs leading-5 text-emerald-800">
                              Evidence: {link.evidence.note}
                            </p>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {link.status !== "accepted" && (
                            <button
                              onClick={() => updateLink(link.id, "accepted")}
                              className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-bold text-white"
                            >
                              Accept
                            </button>
                          )}
                          {link.status !== "rejected" && (
                            <button
                              onClick={() => updateLink(link.id, "rejected")}
                              className="rounded-lg bg-amber-100 px-3 py-2 text-sm font-bold text-amber-800"
                            >
                              Reject
                            </button>
                          )}
                          <button
                            onClick={() => deleteLink(link.id)}
                            className="rounded-lg bg-red-50 px-3 py-2 text-sm font-bold text-red-700"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </section>

      <section className="mt-10 atlas-panel">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-black text-slate-900">Traceability matrix</h2>
            <p className="mt-1 text-sm text-slate-500">
              Rows are requirements; columns are artifacts. Suggested links do not count as coverage.
            </p>
          </div>
          <div className="text-right text-xs text-slate-500">
            <p>Uncovered requirements: {summary.uncovered_requirements}</p>
            <p>Uncovered artifacts: {summary.uncovered_artifacts}</p>
          </div>
        </div>

        {matrix.requirements.length === 0 || matrix.artifacts.length === 0 ? (
          <EmptyState text="The matrix appears after both requirements and artifacts exist." />
        ) : (
          <div className="mt-5 overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full border-collapse text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="sticky left-0 z-10 min-w-64 border-b border-r border-slate-200 bg-slate-50 p-3 text-left font-black text-slate-700">
                    Requirement
                  </th>
                  {matrix.artifacts.map((artifact) => (
                    <th
                      key={artifact.id}
                      className="min-w-40 border-b border-slate-200 p-3 text-center align-bottom"
                    >
                      <p className="text-xs font-black text-indigo-600">{artifact.code}</p>
                      <p className="mt-1 font-bold text-slate-800">{artifact.name}</p>
                      <p className="mt-1 text-xs font-normal text-slate-500">
                        {TYPE_LABELS[artifact.artifact_type]}
                      </p>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.requirements.map((requirement) => (
                  <tr key={requirement.id} className="border-b border-slate-100 last:border-0">
                    <th className="sticky left-0 z-10 border-r border-slate-200 bg-white p-3 text-left">
                      <p className="text-xs font-black text-indigo-600">{requirement.code}</p>
                      <p className="mt-1 font-semibold text-slate-800">{requirement.title}</p>
                    </th>
                    {matrix.artifacts.map((artifact) => {
                      const cell = matrixCellByPair[`${requirement.id}:${artifact.id}`];
                      return (
                        <td key={artifact.id} className="p-3 text-center">
                          {cell ? (
                            <div>
                              <StatusBadge status={cell.status} />
                              <p className="mt-1 text-xs text-slate-500">
                                {(cell.confidence_score * 100).toFixed(0)}%
                              </p>
                            </div>
                          ) : (
                            <span className="text-slate-300">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </AppShell>
  );
}

function ArtifactFields({ form, setForm, errors = {}, clearErrors }) {
  return (
    <>
      <label className="mt-5 block text-sm font-semibold text-slate-700">
        Artifact name
        <input
          required
          minLength={2}
          value={form.name}
          aria-invalid={Boolean(errors.name)}
          onChange={(event) => {
            setForm({ ...form, name: event.target.value });
            if (errors.name) clearErrors?.((current) => ({ ...current, name: "" }));
          }}
          className="atlas-input"
          placeholder="Password reset API"
          maxLength={180}
        />
        <FieldError>{errors.name}</FieldError>
      </label>
      <label className="mt-4 block text-sm font-semibold text-slate-700">
        Type
        <select
          value={form.artifact_type}
          onChange={(event) => setForm({ ...form, artifact_type: event.target.value })}
          className="atlas-select"
        >
          {Object.entries(TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label className="mt-4 block text-sm font-semibold text-slate-700">
        Description
        <textarea
          required
          minLength={5}
          rows={4}
          value={form.description}
          aria-invalid={Boolean(errors.description)}
          onChange={(event) => {
            setForm({ ...form, description: event.target.value });
            if (errors.description) clearErrors?.((current) => ({ ...current, description: "" }));
          }}
          className="atlas-textarea"
          placeholder="Explain the artifact responsibility using requirement vocabulary."
          maxLength={10000}
        />
        <FieldError>{errors.description}</FieldError>
      </label>
      <label className="mt-4 block text-sm font-semibold text-slate-700">
        Technical notes
        <textarea
          rows={3}
          value={form.technical_notes}
          aria-invalid={Boolean(errors.technical_notes)}
          onChange={(event) => {
            setForm({ ...form, technical_notes: event.target.value });
            if (errors.technical_notes) clearErrors?.((current) => ({ ...current, technical_notes: "" }));
          }}
          className="atlas-textarea"
          placeholder="POST /auth/password-reset, users table fields, expected test outcome..."
          maxLength={4000}
        />
        <FieldError>{errors.technical_notes}</FieldError>
      </label>
    </>
  );
}

function SelectField({ label, value, onChange, options, blankLabel = "Select", error }) {
  return (
    <label className="mt-4 block text-sm font-semibold text-slate-700">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="atlas-select"
        aria-invalid={Boolean(error)}
      >
        <option value="">{blankLabel}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <FieldError>{error}</FieldError>
    </label>
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

function EmptyState({ text }) {
  return (
    <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    suggested: "bg-indigo-50 text-indigo-700",
    accepted: "bg-emerald-50 text-emerald-700",
    rejected: "bg-amber-50 text-amber-800",
  };
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-black capitalize ${styles[status]}`}>
      {status}
    </span>
  );
}

function StatusPill({ status, count }) {
  return (
    <span className="rounded-full bg-slate-100 px-3 py-2 capitalize text-slate-700">
      {status}: {count}
    </span>
  );
}
