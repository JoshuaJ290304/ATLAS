import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import ProjectNav from "../components/ProjectNav";
import { FieldError } from "../components/UI";
import { apiErrorMessage } from "../utils/validation";

const EMPTY_SUMMARY = {
  total: 0,
  low: 0,
  medium: 0,
  high: 0,
  critical: 0,
  latest_risk_score: null,
  latest_severity: null,
};

const SEVERITY_STYLES = {
  low: "bg-emerald-50 text-emerald-700",
  medium: "bg-amber-50 text-amber-800",
  high: "bg-orange-50 text-orange-800",
  critical: "bg-red-50 text-red-700",
};

export default function ImpactAnalysisPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [requirements, setRequirements] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [requirementId, setRequirementId] = useState("");
  const [versions, setVersions] = useState([]);
  const [baselineVersion, setBaselineVersion] = useState("");
  const [targetVersion, setTargetVersion] = useState("");
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [formError, setFormError] = useState("");

  async function loadWorkspace() {
    setLoading(true);
    setError("");
    try {
      const [projectResponse, requirementsResponse, analysesResponse, summaryResponse] =
        await Promise.all([
          api.get(`/projects/${projectId}`),
          api.get(`/projects/${projectId}/requirements`),
          api.get(`/projects/${projectId}/impact-analyses`),
          api.get(`/projects/${projectId}/impact-analyses/summary`),
        ]);
      setProject(projectResponse.data);
      setRequirements(requirementsResponse.data);
      setAnalyses(analysesResponse.data);
      setSummary(summaryResponse.data);
      setSelectedAnalysis((current) => current || analysesResponse.data[0] || null);
      setRequirementId((current) => current || requirementsResponse.data[0]?.id || "");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not load impact-analysis data.");
    } finally {
      setLoading(false);
    }
  }

  async function loadVersions(selectedRequirementId) {
    if (!selectedRequirementId) {
      setVersions([]);
      setBaselineVersion("");
      setTargetVersion("");
      return;
    }
    try {
      const response = await api.get(
        `/projects/${projectId}/requirements/${selectedRequirementId}/versions`,
      );
      setVersions(response.data);
      if (response.data.length >= 2) {
        setBaselineVersion(String(response.data.at(-2).version));
        setTargetVersion(String(response.data.at(-1).version));
      } else {
        setBaselineVersion("");
        setTargetVersion(response.data[0] ? String(response.data[0].version) : "");
      }
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not load requirement versions.");
    }
  }

  useEffect(() => {
    loadWorkspace();
  }, [projectId]);

  useEffect(() => {
    loadVersions(requirementId);
  }, [requirementId, projectId]);

  const selectedRequirement = useMemo(
    () => requirements.find((item) => item.id === requirementId),
    [requirements, requirementId],
  );

  async function runAnalysis(event) {
    event.preventDefault();
    let validationMessage = "";
    if (!requirementId) validationMessage = "Select a requirement.";
    else if (!baselineVersion || !targetVersion) validationMessage = "Select both baseline and target versions.";
    else if (Number(baselineVersion) >= Number(targetVersion)) validationMessage = "Baseline version must be lower than target version.";
    setFormError(validationMessage);
    if (validationMessage) return;
    setAnalyzing(true);
    setError("");
    setNotice("");
    try {
      const response = await api.post(`/projects/${projectId}/impact-analyses`, {
        requirement_id: requirementId,
        baseline_version: Number(baselineVersion),
        target_version: Number(targetVersion),
      });
      setSelectedAnalysis(response.data);
      setNotice(
        `Impact report created: ${response.data.severity} risk (${response.data.risk_score}/100).`,
      );
      await loadWorkspace();
      setSelectedAnalysis(response.data);
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not run impact analysis."));
    } finally {
      setAnalyzing(false);
    }
  }

  async function deleteAnalysis(analysisId) {
    if (!window.confirm("Delete this stored impact report?")) return;
    try {
      await api.delete(`/projects/${projectId}/impact-analyses/${analysisId}`);
      setSelectedAnalysis(null);
      setNotice("Impact report deleted.");
      await loadWorkspace();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not delete the report.");
    }
  }

  const validSelection =
    requirementId && baselineVersion && targetVersion && Number(baselineVersion) < Number(targetVersion);

  return (
    <AppShell>
      <ProjectNav projectId={projectId} />

      <section className="atlas-page-header">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-indigo-600">
            Milestone 5
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            {project?.name || "Change-impact analysis"}
          </h1>
          <p className="mt-4 max-w-3xl leading-7 text-slate-600">
            Compare requirement versions, follow accepted trace links, calculate a reproducible
            risk score, and preserve each report for later review.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Metric label="Reports" value={summary.total} />
          <Metric label="High" value={summary.high} />
          <Metric label="Critical" value={summary.critical} />
          <Metric label="Latest score" value={summary.latest_risk_score ?? "—"} />
          <Metric label="Latest severity" value={summary.latest_severity || "—"} />
          <Metric label="Requirements" value={requirements.length} />
        </div>
      </section>

      {(error || notice) && (
        <section className="mt-6 space-y-3">
          {error && <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
          {notice && <p className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{notice}</p>}
        </section>
      )}

      <section className="mt-10 grid gap-8 xl:grid-cols-[380px_minmax(0,1fr)]">
        <div className="space-y-6">
          <form onSubmit={runAnalysis} noValidate className="atlas-panel">
            <h2 className="text-xl font-black text-slate-900">Run impact analysis</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Edit a requirement at least once so two persisted versions are available.
            </p>
            <label className="mt-5 block text-sm font-semibold text-slate-700">
              Requirement
              <select
                value={requirementId}
                onChange={(event) => { setRequirementId(event.target.value); setFormError(""); }}
                className="atlas-select"
              >
                <option value="">Select a requirement</option>
                {requirements.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.code} — {item.title}
                  </option>
                ))}
              </select>
            </label>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <VersionSelect
                label="Baseline"
                value={baselineVersion}
                onChange={setBaselineVersion}
                versions={versions.filter((item) => item.version < Number(targetVersion || Infinity))}
              />
              <VersionSelect
                label="Target"
                value={targetVersion}
                onChange={setTargetVersion}
                versions={versions.filter((item) => item.version > Number(baselineVersion || 0))}
              />
            </div>
            <FieldError>{formError}</FieldError>
            {selectedRequirement && (
              <p className="mt-4 rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-600">
                Current requirement version: {selectedRequirement.version}. Stored snapshots: {versions.length}.
              </p>
            )}
            {versions.length < 2 && requirementId && (
              <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
                Open Requirements, edit this requirement, and save it to create the next version.
              </p>
            )}
            <button
              disabled={!validSelection || analyzing}
              className="mt-5 w-full rounded-xl bg-indigo-600 px-4 py-3 font-bold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {analyzing ? "Analyzing change..." : "Generate impact report"}
            </button>
          </form>

          <section className="atlas-panel">
            <h2 className="text-xl font-black text-slate-900">Report history</h2>
            {loading ? (
              <p className="mt-4 text-sm text-slate-500">Loading reports...</p>
            ) : analyses.length === 0 ? (
              <p className="mt-4 text-sm leading-6 text-slate-500">No impact reports yet.</p>
            ) : (
              <div className="mt-4 space-y-3">
                {analyses.map((analysis) => (
                  <button
                    key={analysis.id}
                    onClick={() => setSelectedAnalysis(analysis)}
                    className={`w-full rounded-xl border p-4 text-left transition ${
                      selectedAnalysis?.id === analysis.id
                        ? "border-indigo-400 bg-indigo-50"
                        : "border-slate-200 hover:border-indigo-200"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-black text-indigo-600">{analysis.requirement_code}</p>
                        <p className="mt-1 font-bold text-slate-900">
                          v{analysis.baseline_version} → v{analysis.target_version}
                        </p>
                      </div>
                      <SeverityBadge severity={analysis.severity} />
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                      {new Date(analysis.created_at).toLocaleString()} · {analysis.risk_score}/100
                    </p>
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="min-w-0">
          {selectedAnalysis ? (
            <ImpactReport analysis={selectedAnalysis} onDelete={deleteAnalysis} />
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <p className="font-bold text-slate-800">No report selected</p>
              <p className="mt-2 text-sm text-slate-500">Generate a report or select one from history.</p>
            </div>
          )}
        </div>
      </section>
    </AppShell>
  );
}

function ImpactReport({ analysis, onDelete }) {
  const differences = analysis.differences || {};
  return (
    <article className="space-y-6">
      <section className="atlas-panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-black uppercase tracking-wider text-indigo-600">
              {analysis.requirement_code} · v{analysis.baseline_version} → v{analysis.target_version}
            </p>
            <h2 className="mt-2 text-2xl font-black text-slate-900">{analysis.requirement_title}</h2>
          </div>
          <div className="text-right">
            <SeverityBadge severity={analysis.severity} />
            <p className="mt-2 text-3xl font-black text-slate-900">{analysis.risk_score}/100</p>
          </div>
        </div>
        <p className="mt-5 rounded-xl bg-slate-50 p-4 leading-7 text-slate-700">
          {analysis.change_summary}
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          {(differences.changed_fields || []).map((field) => (
            <span key={field} className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">
              {field.replaceAll("_", " ")}
            </span>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <ArtifactImpactList title="Direct impact" items={analysis.direct_artifacts} />
        <ArtifactImpactList title="Transitive impact" items={analysis.transitive_artifacts} />
      </section>

      <section className="atlas-panel">
        <h3 className="text-xl font-black text-slate-900">Risk-score breakdown</h3>
        <div className="mt-5 space-y-4">
          {analysis.risk_factors.map((factor) => (
            <div key={factor.key}>
              <div className="flex items-center justify-between gap-4 text-sm">
                <p className="font-bold text-slate-800">{factor.label}</p>
                <p className="font-black text-slate-900">{factor.points}/{factor.maximum}</p>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-indigo-600"
                  style={{ width: `${Math.min(100, (factor.points / factor.maximum) * 100)}%` }}
                />
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-500">{factor.explanation}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="atlas-panel">
        <h3 className="text-xl font-black text-slate-900">Version difference</h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <Metric label="Changed text" value={`${Math.round((differences.change_ratio || 0) * 100)}%`} />
          <Metric label="Added terms" value={(differences.added_terms || []).length} />
          <Metric label="Removed terms" value={(differences.removed_terms || []).length} />
        </div>
        {(differences.unified_diff || []).length > 0 && (
          <pre className="mt-5 max-h-80 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-4 text-xs leading-5 text-slate-100">
            {(differences.unified_diff || []).join("\n")}
          </pre>
        )}
        <button
          onClick={() => onDelete(analysis.id)}
          className="mt-5 rounded-lg bg-red-50 px-4 py-2 text-sm font-bold text-red-700 hover:bg-red-100"
        >
          Delete report
        </button>
      </section>
    </article>
  );
}

function ArtifactImpactList({ title, items }) {
  return (
    <section className="atlas-panel">
      <h3 className="text-xl font-black text-slate-900">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-4 text-sm leading-6 text-slate-500">No artifacts were found on this path.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {items.map((item) => (
            <div key={item.id} className="rounded-xl border border-slate-200 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-black text-indigo-600">{item.code}</p>
                  <p className="mt-1 font-bold text-slate-900">{item.name}</p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
                  {item.artifact_type.replaceAll("_", " ")}
                </span>
              </div>
              <p className="mt-3 text-xs leading-5 text-slate-500">Path: {item.path.join(" → ")}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function VersionSelect({ label, value, onChange, versions }) {
  return (
    <label className="block text-sm font-semibold text-slate-700">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-3"
      >
        <option value="">Version</option>
        {versions.map((item) => (
          <option key={item.id} value={item.version}>
            v{item.version}
          </option>
        ))}
      </select>
    </label>
  );
}

function SeverityBadge({ severity }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-black uppercase ${SEVERITY_STYLES[severity] || "bg-slate-100 text-slate-700"}`}>
      {severity}
    </span>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-2 break-words text-2xl font-black capitalize text-slate-900">{value}</p>
    </div>
  );
}
