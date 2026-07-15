import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import ProjectNav from "../components/ProjectNav";
import { FieldError } from "../components/UI";
import { apiErrorMessage, clean, validateRequired } from "../utils/validation";

const EMPTY_MANUAL = {
  title: "",
  description: "",
  requirement_type: "functional",
  non_functional_category: "",
  status: "draft",
};

export default function RequirementsPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [requirements, setRequirements] = useState([]);
  const [summary, setSummary] = useState(emptySummary());
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [filters, setFilters] = useState({ type: "all", status: "all", ambiguous: false });
  const [manual, setManual] = useState(EMPTY_MANUAL);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [manualErrors, setManualErrors] = useState({});
  const [editErrors, setEditErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadWorkspace() {
    setLoading(true);
    setError("");
    try {
      const [projectResponse, documentsResponse, requirementsResponse, summaryResponse] =
        await Promise.all([
          api.get(`/projects/${projectId}`),
          api.get(`/projects/${projectId}/documents`),
          api.get(`/projects/${projectId}/requirements`),
          api.get(`/projects/${projectId}/requirements/summary`),
        ]);
      setProject(projectResponse.data);
      setDocuments(documentsResponse.data);
      setRequirements(requirementsResponse.data);
      setSummary(summaryResponse.data);

      const extractedDocuments = documentsResponse.data.filter(
        (document) => document.status === "extracted",
      );
      if (!selectedDocumentId && extractedDocuments.length > 0) {
        setSelectedDocumentId(extractedDocuments[0].id);
      }
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not load requirement intelligence.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkspace();
  }, [projectId]);

  const extractedDocuments = useMemo(
    () => documents.filter((document) => document.status === "extracted"),
    [documents],
  );

  const visibleRequirements = useMemo(
    () =>
      requirements.filter((requirement) => {
        if (filters.type !== "all" && requirement.requirement_type !== filters.type) return false;
        if (filters.status !== "all" && requirement.status !== filters.status) return false;
        if (filters.ambiguous && requirement.ambiguity_score === 0) return false;
        return true;
      }),
    [requirements, filters],
  );

  async function runExtraction(event) {
    event.preventDefault();
    if (!selectedDocumentId) {
      setError("Select an extracted PDF or DOCX document first.");
      return;
    }

    setExtracting(true);
    setError("");
    setNotice("");
    try {
      const response = await api.post(
        `/projects/${projectId}/requirements/extract`,
        { document_id: selectedDocumentId, replace_existing: replaceExisting },
        { timeout: 60000 },
      );
      setNotice(
        `Detected ${response.data.detected_count}; created ${response.data.created_count}; ` +
          `skipped ${response.data.skipped_duplicate_count} duplicate(s).`,
      );
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Requirement extraction failed.");
    } finally {
      setExtracting(false);
    }
  }


  function validateRequirementForm(values) {
    const next = {
      title: validateRequired(values.title, "Requirement title", 3, 180),
      description: validateRequired(values.description, "Requirement description", 10, 10000),
      non_functional_category:
        values.requirement_type === "non_functional"
          ? validateRequired(values.non_functional_category, "Non-functional category", 2, 80)
          : "",
    };
    Object.keys(next).forEach((key) => !next[key] && delete next[key]);
    return next;
  }

  async function createManualRequirement(event) {
    event.preventDefault();
    const validationErrors = validateRequirementForm(manual);
    setManualErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const payload = {
        ...manual,
        title: clean(manual.title),
        description: clean(manual.description),
        non_functional_category:
          manual.requirement_type === "non_functional"
            ? clean(manual.non_functional_category) || null
            : null,
      };
      await api.post(`/projects/${projectId}/requirements`, payload);
      setManual(EMPTY_MANUAL);
      setManualErrors({});
      setNotice("Manual requirement created.");
      await loadWorkspace();
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not create the requirement."));
    } finally {
      setSaving(false);
    }
  }

  function beginEdit(requirement) {
    setEditingId(requirement.id);
    setEditForm({
      title: requirement.title,
      description: requirement.description,
      requirement_type: requirement.requirement_type,
      non_functional_category: requirement.non_functional_category || "",
      status: requirement.status,
    });
    setError("");
    setNotice("");
    setEditErrors({});
  }

  async function saveRequirement(event, requirementId) {
    event.preventDefault();
    const validationErrors = validateRequirementForm(editForm);
    setEditErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;
    setSaving(true);
    setError("");
    try {
      const payload = {
        ...editForm,
        title: clean(editForm.title),
        description: clean(editForm.description),
        non_functional_category:
          editForm.requirement_type === "non_functional"
            ? clean(editForm.non_functional_category) || null
            : null,
      };
      const response = await api.patch(
        `/projects/${projectId}/requirements/${requirementId}`,
        payload,
      );
      setRequirements((current) =>
        current.map((requirement) =>
          requirement.id === requirementId ? response.data : requirement,
        ),
      );
      setEditingId(null);
      setEditForm(null);
      setEditErrors({});
      setNotice(`Requirement ${response.data.code} updated to version ${response.data.version}.`);
      const summaryResponse = await api.get(`/projects/${projectId}/requirements/summary`);
      setSummary(summaryResponse.data);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not update the requirement."));
    } finally {
      setSaving(false);
    }
  }

  async function deleteRequirement(requirement) {
    const confirmed = window.confirm(`Delete ${requirement.code}: ${requirement.title}?`);
    if (!confirmed) return;

    setError("");
    setNotice("");
    try {
      await api.delete(`/projects/${projectId}/requirements/${requirement.id}`);
      setNotice(`${requirement.code} deleted.`);
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not delete the requirement.");
    }
  }

  return (
    <AppShell>
      <ProjectNav projectId={projectId} />

      <section className="atlas-page-header">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-indigo-600">
            Milestone 3
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            {project?.name || "Requirement intelligence"}
          </h1>
          <p className="mt-4 max-w-3xl leading-7 text-slate-600">
            Detect requirement statements, classify functional and non-functional behavior, flag
            ambiguous wording, and review every record before traceability links are created.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Metric label="Total" value={summary.total} />
          <Metric label="Functional" value={summary.functional} />
          <Metric label="Non-functional" value={summary.non_functional} />
          <Metric label="Needs review" value={summary.ambiguous} />
        </div>
      </section>

      {(error || notice) && (
        <section className="mt-6">
          {error && <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
          {notice && (
            <p className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{notice}</p>
          )}
        </section>
      )}

      <section className="mt-10 grid gap-8 xl:grid-cols-[360px_1fr]">
        <div className="space-y-6">
          <form
            onSubmit={runExtraction}
            className="atlas-panel"
          >
            <h2 className="text-xl font-black text-slate-900">Extract from document</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Deterministic rules detect obligation statements and preserve source positions.
            </p>

            <label className="mt-5 block text-sm font-semibold text-slate-700">
              Source document
              <select
                value={selectedDocumentId}
                onChange={(event) => setSelectedDocumentId(event.target.value)}
                className="atlas-select"
              >
                <option value="">Select document</option>
                {extractedDocuments.map((document) => (
                  <option key={document.id} value={document.id}>
                    {document.original_filename}
                  </option>
                ))}
              </select>
            </label>

            {extractedDocuments.length === 0 && (
              <p className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-700">
                Upload and extract a PDF or DOCX document before running requirement extraction.
              </p>
            )}

            <label className="mt-4 flex items-start gap-3 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={replaceExisting}
                onChange={(event) => setReplaceExisting(event.target.checked)}
                className="mt-1"
              />
              Replace previously auto-extracted requirements from this document. Manual records
              are preserved.
            </label>

            <button
              disabled={extracting || extractedDocuments.length === 0}
              className="mt-5 w-full rounded-xl bg-indigo-600 px-4 py-3 font-bold text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {extracting ? "Analyzing document..." : "Extract requirements"}
            </button>
          </form>

          <form
            onSubmit={createManualRequirement}
            noValidate
            className="atlas-panel"
          >
            <h2 className="text-xl font-black text-slate-900">Add manual requirement</h2>
            <RequirementFields form={manual} setForm={setManual} errors={manualErrors} clearErrors={setManualErrors} />
            <button
              disabled={saving}
              className="mt-5 w-full rounded-xl bg-slate-900 px-4 py-3 font-bold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {saving ? "Saving..." : "Add requirement"}
            </button>
          </form>
        </div>

        <div>
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <h2 className="text-2xl font-black text-slate-900">Requirement register</h2>
              <p className="mt-1 text-sm text-slate-500">
                {visibleRequirements.length} of {requirements.length} requirement(s) shown
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <select
                value={filters.type}
                onChange={(event) => setFilters({ ...filters, type: event.target.value })}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option value="all">All types</option>
                <option value="functional">Functional</option>
                <option value="non_functional">Non-functional</option>
              </select>
              <select
                value={filters.status}
                onChange={(event) => setFilters({ ...filters, status: event.target.value })}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option value="all">All statuses</option>
                <option value="draft">Draft</option>
                <option value="reviewed">Reviewed</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
              <label className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.ambiguous}
                  onChange={(event) =>
                    setFilters({ ...filters, ambiguous: event.target.checked })
                  }
                />
                Ambiguous only
              </label>
              <button
                type="button"
                onClick={loadWorkspace}
                className="rounded-lg px-3 py-2 text-sm font-bold text-indigo-700 hover:bg-indigo-50"
              >
                Refresh
              </button>
            </div>
          </div>

          {loading ? (
            <p className="mt-5 text-slate-500">Loading requirements...</p>
          ) : visibleRequirements.length === 0 ? (
            <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <p className="font-bold text-slate-800">No matching requirements</p>
              <p className="mt-2 text-sm text-slate-500">
                Extract requirements from a document or create one manually.
              </p>
            </div>
          ) : (
            <div className="mt-5 space-y-4">
              {visibleRequirements.map((requirement) =>
                editingId === requirement.id ? (
                  <form
                    key={requirement.id}
                    onSubmit={(event) => saveRequirement(event, requirement.id)}
                    noValidate
                    className="rounded-2xl border-2 border-indigo-200 bg-white p-6 shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <h3 className="font-black text-slate-900">
                        Edit {requirement.code} · version {requirement.version}
                      </h3>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingId(null);
                          setEditForm(null);
                        }}
                        className="text-sm font-bold text-slate-500 hover:text-slate-800"
                      >
                        Cancel
                      </button>
                    </div>
                    <RequirementFields form={editForm} setForm={setEditForm} errors={editErrors} clearErrors={setEditErrors} />
                    <button
                      disabled={saving}
                      className="mt-5 rounded-xl bg-indigo-600 px-5 py-3 font-bold text-white disabled:opacity-60"
                    >
                      {saving ? "Saving..." : "Save changes"}
                    </button>
                  </form>
                ) : (
                  <RequirementCard
                    key={requirement.id}
                    requirement={requirement}
                    document={documents.find(
                      (document) => document.id === requirement.source_document_id,
                    )}
                    onEdit={() => beginEdit(requirement)}
                    onDelete={() => deleteRequirement(requirement)}
                  />
                ),
              )}
            </div>
          )}
        </div>
      </section>
    </AppShell>
  );
}

function RequirementFields({ form, setForm, errors = {}, clearErrors }) {
  return (
    <div className="mt-5 space-y-4">
      <label className="block text-sm font-semibold text-slate-700">
        Title
        <input
          required
          minLength={3}
          maxLength={180}
          value={form.title}
          aria-invalid={Boolean(errors.title)}
          onChange={(event) => {
            setForm({ ...form, title: event.target.value });
            if (errors.title) clearErrors?.((current) => ({ ...current, title: "" }));
          }}
          className="atlas-input"
          placeholder="Allow users to reset forgotten passwords"
        />
        <FieldError>{errors.title}</FieldError>
      </label>
      <label className="block text-sm font-semibold text-slate-700">
        Description
        <textarea
          required
          minLength={10}
          rows={5}
          value={form.description}
          aria-invalid={Boolean(errors.description)}
          onChange={(event) => {
            setForm({ ...form, description: event.target.value });
            if (errors.description) clearErrors?.((current) => ({ ...current, description: "" }));
          }}
          className="atlas-textarea"
          placeholder="The system shall allow a registered user to reset a forgotten password."
        />
        <FieldError>{errors.description}</FieldError>
      </label>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-semibold text-slate-700">
          Type
          <select
            value={form.requirement_type}
            onChange={(event) =>
              setForm({
                ...form,
                requirement_type: event.target.value,
                non_functional_category:
                  event.target.value === "functional" ? "" : form.non_functional_category,
              })
            }
            className="atlas-select"
          >
            <option value="functional">Functional</option>
            <option value="non_functional">Non-functional</option>
          </select>
        </label>
        <label className="block text-sm font-semibold text-slate-700">
          Status
          <select
            value={form.status}
            onChange={(event) => setForm({ ...form, status: event.target.value })}
            className="atlas-select"
          >
            <option value="draft">Draft</option>
            <option value="reviewed">Reviewed</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </label>
      </div>
      {form.requirement_type === "non_functional" && (
        <label className="block text-sm font-semibold text-slate-700">
          Non-functional category
          <input
            maxLength={80}
            value={form.non_functional_category}
            aria-invalid={Boolean(errors.non_functional_category)}
            onChange={(event) => {
              setForm({ ...form, non_functional_category: event.target.value });
              if (errors.non_functional_category) clearErrors?.((current) => ({ ...current, non_functional_category: "" }));
            }}
            className="atlas-input"
            placeholder="security, performance, usability..."
          />
          <FieldError>{errors.non_functional_category}</FieldError>
        </label>
      )}
    </div>
  );
}

function RequirementCard({ requirement, document, onEdit, onDelete }) {
  return (
    <article className="atlas-panel">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-sm font-black text-indigo-700">{requirement.code}</span>
            <Badge value={requirement.requirement_type.replace("_", "-")} kind="type" />
            <Badge value={requirement.status} kind="status" />
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold capitalize text-slate-600">
              {requirement.source}
            </span>
          </div>
          <h3 className="mt-3 text-lg font-black text-slate-900">{requirement.title}</h3>
          <p className="mt-3 whitespace-pre-wrap leading-7 text-slate-600">
            {requirement.description}
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={onEdit}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-bold text-slate-700 hover:bg-slate-50"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="rounded-lg border border-red-200 px-3 py-2 text-sm font-bold text-red-700 hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      </div>

      {requirement.ambiguity_flags.length > 0 && (
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-black text-amber-800">
            Ambiguity score: {requirement.ambiguity_score}/100
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">
            {requirement.ambiguity_flags.map((flag) => (
              <li key={flag}>{flag}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-5 grid gap-3 border-t border-slate-100 pt-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <Fact label="Confidence" value={`${Math.round(requirement.confidence_score * 100)}%`} />
        <Fact
          label="Category"
          value={requirement.non_functional_category || "Not applicable"}
        />
        <Fact label="Version" value={requirement.version} />
        <Fact
          label="Source"
          value={document?.original_filename || (requirement.source === "manual" ? "Manual" : "Deleted document")}
        />
      </div>
    </article>
  );
}

function Badge({ value, kind }) {
  const classes =
    kind === "type"
      ? value === "functional"
        ? "bg-blue-50 text-blue-700"
        : "bg-purple-50 text-purple-700"
      : value === "approved"
        ? "bg-emerald-50 text-emerald-700"
        : value === "rejected"
          ? "bg-red-50 text-red-700"
          : value === "reviewed"
            ? "bg-cyan-50 text-cyan-700"
            : "bg-amber-50 text-amber-700";

  return (
    <span className={`rounded-full px-3 py-1 text-xs font-bold capitalize ${classes}`}>
      {value}
    </span>
  );
}

function Fact({ label, value }) {
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-1 break-words font-semibold capitalize text-slate-700">{value}</p>
    </div>
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

function emptySummary() {
  return {
    total: 0,
    functional: 0,
    non_functional: 0,
    ambiguous: 0,
    draft: 0,
    reviewed: 0,
    approved: 0,
    rejected: 0,
    categories: {},
  };
}
