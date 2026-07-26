import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import Icon from "../components/Icon";
import ProjectNav from "../components/ProjectNav";
import { Alert, EmptyState, LoadingState, ProgressBar } from "../components/UI";

const emptyForm = {
  name: "",
  version_label: "",
  description: "",
  target_date: "",
  release_owner: "",
  baseline_id: "",
  selected_requirement_ids: [],
  selected_test_case_ids: [],
  minimum_traceability_percent: 80,
  minimum_test_coverage_percent: 80,
  maximum_high_risk_impacts: 0,
  maximum_overdue_reviews: 0,
  require_active_baseline: true,
  require_approved_requirements: true,
};

const statusLabel = (value) => (value || "not_evaluated").replaceAll("_", " ");

function Metric({ label, value, detail }) {
  return (
    <div className="atlas-metric-card">
      <p className="atlas-metric-label">{label}</p>
      <p className="atlas-metric-value">{value}</p>
      {detail && <p className="atlas-metric-detail">{detail}</p>}
    </div>
  );
}

function GateBadge({ status }) {
  return <span className={`atlas-gate-badge is-${status}`}>{statusLabel(status)}</span>;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function ReleaseReadinessPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [releases, setReleases] = useState([]);
  const [requirements, setRequirements] = useState([]);
  const [testCases, setTestCases] = useState([]);
  const [baselines, setBaselines] = useState([]);
  const [summary, setSummary] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [compareSource, setCompareSource] = useState("");
  const [compareTarget, setCompareTarget] = useState("");
  const [decision, setDecision] = useState({ reviewer_name: "", review_comments: "", decision_reason: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const selected = useMemo(
    () => releases.find((release) => release.id === selectedId) || null,
    [releases, selectedId],
  );

  const load = async (preserveSelection = true) => {
    setLoading(true);
    try {
      const [projectResponse, releaseResponse, requirementResponse, testResponse, baselineResponse, summaryResponse] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/releases`),
        api.get(`/projects/${projectId}/requirements`),
        api.get(`/projects/${projectId}/test-cases`),
        api.get(`/projects/${projectId}/governance/baselines`),
        api.get(`/projects/${projectId}/releases/summary`),
      ]);
      setProject(projectResponse.data);
      setReleases(releaseResponse.data);
      setRequirements(requirementResponse.data);
      setTestCases(testResponse.data);
      setBaselines(baselineResponse.data);
      setSummary(summaryResponse.data);
      const nextSelection = preserveSelection && selectedId
        ? releaseResponse.data.find((item) => item.id === selectedId)?.id
        : releaseResponse.data[0]?.id;
      setSelectedId(nextSelection || null);
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to load release readiness." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(false); }, [projectId]);

  useEffect(() => {
    if (!selected) {
      setEvaluation(null);
      return;
    }
    const results = selected.gate_summary?.results || [];
    setEvaluation(results.length ? {
      readiness_score: selected.readiness_score,
      readiness_label: selected.readiness_label,
      gate_results: results,
      blockers: selected.blockers || [],
      recommendations: selected.recommendations || [],
    } : null);
  }, [selected]);

  const toggleSelection = (key, id) => {
    setForm((current) => ({
      ...current,
      [key]: current[key].includes(id)
        ? current[key].filter((value) => value !== id)
        : [...current[key], id],
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!form.name.trim() || !form.version_label.trim() || !form.release_owner.trim()) {
      setMessage({ type: "error", text: "Release name, version, and owner are required." });
      return;
    }
    if (!form.selected_requirement_ids.length) {
      setMessage({ type: "error", text: "Select at least one requirement for the release candidate." });
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        baseline_id: form.baseline_id || null,
        target_date: form.target_date || null,
        minimum_traceability_percent: Number(form.minimum_traceability_percent),
        minimum_test_coverage_percent: Number(form.minimum_test_coverage_percent),
        maximum_high_risk_impacts: Number(form.maximum_high_risk_impacts),
        maximum_overdue_reviews: Number(form.maximum_overdue_reviews),
      };
      if (editingId) {
        await api.put(`/projects/${projectId}/releases/${editingId}`, payload);
      } else {
        await api.post(`/projects/${projectId}/releases`, payload);
      }
      setMessage({ type: "success", text: editingId ? "Release candidate updated. Quality-gate results were reset." : "Release candidate created." });
      setForm(emptyForm);
      setEditingId(null);
      await load(false);
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to save release candidate." });
    } finally {
      setSaving(false);
    }
  };

  const beginEdit = (item) => {
    setEditingId(item.id);
    setForm({
      name: item.name,
      version_label: item.version_label,
      description: item.description || "",
      target_date: item.target_date || "",
      release_owner: item.release_owner,
      baseline_id: item.baseline_id || "",
      selected_requirement_ids: item.selected_requirement_ids || [],
      selected_test_case_ids: item.selected_test_case_ids || [],
      minimum_traceability_percent: item.minimum_traceability_percent,
      minimum_test_coverage_percent: item.minimum_test_coverage_percent,
      maximum_high_risk_impacts: item.maximum_high_risk_impacts,
      maximum_overdue_reviews: item.maximum_overdue_reviews,
      require_active_baseline: item.require_active_baseline,
      require_approved_requirements: item.require_approved_requirements,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const evaluate = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const response = await api.post(`/projects/${projectId}/releases/${selected.id}/evaluate`);
      setEvaluation(response.data);
      setMessage({ type: "success", text: `Quality gates evaluated: ${response.data.readiness_label.replaceAll("_", " ")} at ${response.data.readiness_score}%.` });
      await load();
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Quality-gate evaluation failed." });
    } finally {
      setSaving(false);
    }
  };

  const submitForReview = async () => {
    setSaving(true);
    try {
      await api.post(`/projects/${projectId}/releases/${selected.id}/submit`);
      setMessage({ type: "success", text: "Release candidate submitted for sign-off." });
      await load();
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to submit release." });
    } finally {
      setSaving(false);
    }
  };

  const decide = async (approved) => {
    if (!decision.reviewer_name.trim() || decision.decision_reason.trim().length < 5) {
      setMessage({ type: "error", text: "Reviewer name and a clear decision reason are required." });
      return;
    }
    setSaving(true);
    try {
      await api.post(`/projects/${projectId}/releases/${selected.id}/decision`, { ...decision, approved });
      setDecision({ reviewer_name: "", review_comments: "", decision_reason: "" });
      setMessage({ type: "success", text: approved ? "Release candidate approved and ready to publish." : "Release candidate rejected and blocked." });
      await load();
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to record release decision." });
    } finally {
      setSaving(false);
    }
  };

  const publish = async () => {
    if (!window.confirm(`Publish and permanently lock ${selected.version_label}?`)) return;
    setSaving(true);
    try {
      await api.post(`/projects/${projectId}/releases/${selected.id}/publish`);
      setMessage({ type: "success", text: "Release published and locked with an immutable readiness snapshot." });
      await load();
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to publish release." });
    } finally {
      setSaving(false);
    }
  };

  const compare = async () => {
    if (!compareSource || !compareTarget || compareSource === compareTarget) {
      setMessage({ type: "error", text: "Choose two different release candidates to compare." });
      return;
    }
    try {
      const response = await api.post(`/projects/${projectId}/releases/compare`, {
        source_release_id: compareSource,
        target_release_id: compareTarget,
      });
      setComparison(response.data);
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to compare release candidates." });
    }
  };

  const exportReport = async (format) => {
    if (!selected) return;
    try {
      if (format === "json") {
        const response = await api.get(`/projects/${projectId}/releases/${selected.id}/report`);
        downloadBlob(new Blob([JSON.stringify(response.data, null, 2)], { type: "application/json" }), `atlas-${selected.version_label}-readiness.json`);
      } else {
        const response = await api.get(`/projects/${projectId}/releases/${selected.id}/report.csv`, { responseType: "blob" });
        downloadBlob(response.data, `atlas-${selected.version_label}-readiness.csv`);
      }
    } catch (error) {
      setMessage({ type: "error", text: "Unable to export the release report." });
    }
  };

  const remove = async (item) => {
    if (!window.confirm(`Delete ${item.name}?`)) return;
    try {
      await api.delete(`/projects/${projectId}/releases/${item.id}`);
      setMessage({ type: "success", text: "Release candidate deleted." });
      await load(false);
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to delete release candidate." });
    }
  };

  return (
    <AppShell>
      <ProjectNav projectId={projectId} />
      <section className="atlas-page-header atlas-release-header">
        <div>
          <p className="atlas-eyebrow">Release command centre</p>
          <h1>{project?.name || "Release Readiness"}</h1>
          <p>Convert requirements, governance, traceability, impacts, and approved tests into an evidence-based release decision.</p>
        </div>
        <div className="atlas-header-metrics">
          <Metric label="Release candidates" value={summary?.total || 0} />
          <Metric label="Ready" value={summary?.ready || 0} />
          <Metric label="Blocked" value={summary?.blocked || 0} />
          <Metric label="Average readiness" value={`${summary?.average_readiness_score || 0}%`} detail={`${summary?.released || 0} published`} />
        </div>
      </section>

      {message && <div className="mb-5"><Alert type={message.type} onClose={() => setMessage(null)}>{message.text}</Alert></div>}
      {loading ? <LoadingState label="Loading release evidence..." /> : (
        <>
          <div className="atlas-release-workspace">
            <section className="atlas-panel atlas-release-builder">
              <div className="atlas-panel-heading">
                <div><p className="atlas-eyebrow">{editingId ? "Candidate update" : "Release planning"}</p><h2>{editingId ? "Edit release candidate" : "Create release candidate"}</h2><p>Select the exact evidence and thresholds that define release readiness.</p></div>
              </div>
              <form onSubmit={submit} className="grid gap-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="atlas-field"><span>Release name</span><input className="atlas-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="ATLAS Production Release" /></label>
                  <label className="atlas-field"><span>Version</span><input className="atlas-input" value={form.version_label} onChange={(e) => setForm({ ...form, version_label: e.target.value })} placeholder="1.0.0" /></label>
                  <label className="atlas-field"><span>Release owner</span><input className="atlas-input" value={form.release_owner} onChange={(e) => setForm({ ...form, release_owner: e.target.value })} placeholder="Joshua J" /></label>
                  <label className="atlas-field"><span>Target date</span><input type="date" className="atlas-input" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} /></label>
                </div>
                <label className="atlas-field"><span>Description</span><textarea className="atlas-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Scope, release objective, and important constraints." /></label>
                <label className="atlas-field"><span>Active baseline</span><select className="atlas-input" value={form.baseline_id} onChange={(e) => setForm({ ...form, baseline_id: e.target.value })}><option value="">No baseline selected</option>{baselines.map((baseline) => <option key={baseline.id} value={baseline.id}>{baseline.version_label} — {baseline.name} ({baseline.status})</option>)}</select></label>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="atlas-release-selector">
                    <div className="atlas-release-selector-heading"><div><strong>Included requirements</strong><span>{form.selected_requirement_ids.length} selected</span></div><button type="button" onClick={() => setForm({ ...form, selected_requirement_ids: requirements.map((item) => item.id) })}>Select all</button></div>
                    <div>{requirements.map((item) => <label key={item.id}><input type="checkbox" checked={form.selected_requirement_ids.includes(item.id)} onChange={() => toggleSelection("selected_requirement_ids", item.id)} /><span><strong>{item.code}</strong><small>{item.title}</small><em>{item.status}</em></span></label>)}</div>
                  </div>
                  <div className="atlas-release-selector">
                    <div className="atlas-release-selector-heading"><div><strong>Included test cases</strong><span>{form.selected_test_case_ids.length} selected</span></div><button type="button" onClick={() => setForm({ ...form, selected_test_case_ids: testCases.map((item) => item.id) })}>Select all</button></div>
                    <div>{testCases.map((item) => <label key={item.id}><input type="checkbox" checked={form.selected_test_case_ids.includes(item.id)} onChange={() => toggleSelection("selected_test_case_ids", item.id)} /><span><strong>{item.code}</strong><small>{item.title}</small><em>{item.status}</em></span></label>)}</div>
                  </div>
                </div>

                <div className="atlas-threshold-grid">
                  <label className="atlas-field"><span>Minimum traceability %</span><input type="number" min="0" max="100" className="atlas-input" value={form.minimum_traceability_percent} onChange={(e) => setForm({ ...form, minimum_traceability_percent: e.target.value })} /></label>
                  <label className="atlas-field"><span>Minimum approved test %</span><input type="number" min="0" max="100" className="atlas-input" value={form.minimum_test_coverage_percent} onChange={(e) => setForm({ ...form, minimum_test_coverage_percent: e.target.value })} /></label>
                  <label className="atlas-field"><span>Allowed high-risk impacts</span><input type="number" min="0" className="atlas-input" value={form.maximum_high_risk_impacts} onChange={(e) => setForm({ ...form, maximum_high_risk_impacts: e.target.value })} /></label>
                  <label className="atlas-field"><span>Allowed overdue reviews</span><input type="number" min="0" className="atlas-input" value={form.maximum_overdue_reviews} onChange={(e) => setForm({ ...form, maximum_overdue_reviews: e.target.value })} /></label>
                </div>
                <div className="flex flex-wrap gap-3">
                  <label className="atlas-chip"><input type="checkbox" checked={form.require_active_baseline} onChange={(e) => setForm({ ...form, require_active_baseline: e.target.checked })} /> Require active baseline</label>
                  <label className="atlas-chip"><input type="checkbox" checked={form.require_approved_requirements} onChange={(e) => setForm({ ...form, require_approved_requirements: e.target.checked })} /> Require approved requirements</label>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button className="atlas-button atlas-button-primary" disabled={saving}><Icon name="plus" className="h-4 w-4" />{editingId ? "Save candidate" : "Create candidate"}</button>
                  {editingId && <button type="button" className="atlas-button atlas-button-secondary" onClick={() => { setEditingId(null); setForm(emptyForm); }}>Cancel</button>}
                </div>
              </form>
            </section>

            <aside className="atlas-panel atlas-release-list">
              <div className="atlas-panel-heading"><div><p className="atlas-eyebrow">Release portfolio</p><h2>Candidates</h2><p>Select a candidate to inspect gates, sign-off, reports, and publication.</p></div></div>
              <div className="grid gap-3">
                {releases.length === 0 ? <EmptyState icon="release" title="No release candidates" description="Create the first candidate using the release planning form." /> : releases.map((item) => (
                  <button type="button" key={item.id} className={`atlas-release-card ${selectedId === item.id ? "is-selected" : ""}`} onClick={() => setSelectedId(item.id)}>
                    <div><span>{item.version_label}</span><GateBadge status={item.status} /></div>
                    <strong>{item.name}</strong>
                    <p>{item.description || "No release description."}</p>
                    <div className="atlas-release-card-score"><span>{statusLabel(item.readiness_label)}</span><b>{item.readiness_score}%</b></div>
                    <ProgressBar value={item.readiness_score} tone={item.readiness_label === "ready" ? "emerald" : item.readiness_label === "blocked" ? "rose" : "indigo"} />
                  </button>
                ))}
              </div>
            </aside>
          </div>

          {selected && (
            <section className="atlas-panel atlas-release-evidence mt-6">
              <div className="atlas-panel-heading atlas-release-evidence-heading">
                <div><p className="atlas-eyebrow">Quality-gate evidence</p><h2>{selected.version_label} · {selected.name}</h2><p>{selected.selected_requirement_ids.length} requirements · {selected.selected_test_case_ids.length} test cases · owner {selected.release_owner}</p></div>
                <div className="flex flex-wrap gap-2">
                  {selected.status !== "released" && <button type="button" className="atlas-button atlas-button-primary" onClick={evaluate} disabled={saving}><Icon name="activity" className="h-4 w-4" />Evaluate gates</button>}
                  {selected.status !== "released" && <button type="button" className="atlas-button atlas-button-secondary" onClick={() => beginEdit(selected)}><Icon name="edit" className="h-4 w-4" />Edit</button>}
                  <button type="button" className="atlas-button atlas-button-secondary" onClick={() => exportReport("json")}><Icon name="download" className="h-4 w-4" />JSON</button>
                  <button type="button" className="atlas-button atlas-button-secondary" onClick={() => exportReport("csv")}><Icon name="download" className="h-4 w-4" />CSV</button>
                  {selected.status !== "released" && <button type="button" className="atlas-button atlas-button-danger" onClick={() => remove(selected)}><Icon name="trash" className="h-4 w-4" />Delete</button>}
                </div>
              </div>

              <div className="atlas-release-scoreboard">
                <div className={`atlas-readiness-score is-${selected.readiness_label}`}><span>Readiness score</span><strong>{selected.readiness_score}%</strong><em>{statusLabel(selected.readiness_label)}</em></div>
                <div className="atlas-release-gate-counts">
                  {['passed','failed','warning','not_evaluated'].map((key) => <div key={key}><span>{statusLabel(key)}</span><strong>{selected.gate_summary?.counts?.[key] || 0}</strong></div>)}
                </div>
              </div>

              {!evaluation ? <EmptyState icon="activity" title="Quality gates not evaluated" description="Run the evidence engine to calculate readiness, blockers, and corrective actions." /> : (
                <>
                  <div className="atlas-gate-grid">
                    {evaluation.gate_results.map((gate) => (
                      <article key={gate.key} className={`atlas-gate-card is-${gate.status}`}>
                        <div><div><GateBadge status={gate.status} />{gate.critical && <span className="atlas-critical-label">Critical</span>}</div><strong>{gate.name}</strong></div>
                        <p>{gate.message}</p>
                        <dl><div><dt>Measured</dt><dd>{String(gate.measured_value ?? "—")}</dd></div><div><dt>Threshold</dt><dd>{String(gate.threshold ?? "—")}</dd></div><div><dt>Weight</dt><dd>{gate.score_weight}%</dd></div></dl>
                        {gate.recommendation && <small>{gate.recommendation}</small>}
                      </article>
                    ))}
                  </div>
                  {(evaluation.blockers?.length > 0 || evaluation.recommendations?.length > 0) && <div className="atlas-release-actions-grid">
                    <div><h3>Release blockers</h3>{evaluation.blockers?.length ? <ul>{evaluation.blockers.map((item) => <li key={item.gate}><strong>{item.name}</strong><span>{item.message}</span></li>)}</ul> : <p>No critical blockers.</p>}</div>
                    <div><h3>Corrective recommendations</h3>{evaluation.recommendations?.length ? <ol>{evaluation.recommendations.map((item) => <li key={item}>{item}</li>)}</ol> : <p>No corrective action required.</p>}</div>
                  </div>}
                </>
              )}

              {selected.status !== "released" && (
                <div className="atlas-signoff-panel">
                  <div><p className="atlas-eyebrow">Release governance</p><h3>Review, sign-off, and publish</h3><p>Only a fully Ready candidate can be approved and locked as a released version.</p></div>
                  {selected.status !== "in_review" && selected.status !== "ready" ? <button type="button" className="atlas-button atlas-button-secondary" onClick={submitForReview} disabled={saving || selected.readiness_label === "not_evaluated"}><Icon name="send" className="h-4 w-4" />Submit for review</button> : null}
                  {selected.status === "in_review" && <div className="atlas-signoff-form">
                    <input className="atlas-input" placeholder="Reviewer name" value={decision.reviewer_name} onChange={(e) => setDecision({ ...decision, reviewer_name: e.target.value })} />
                    <textarea className="atlas-input" placeholder="Review comments" value={decision.review_comments} onChange={(e) => setDecision({ ...decision, review_comments: e.target.value })} />
                    <textarea className="atlas-input" placeholder="Decision reason" value={decision.decision_reason} onChange={(e) => setDecision({ ...decision, decision_reason: e.target.value })} />
                    <div className="flex flex-wrap gap-2"><button type="button" className="atlas-button atlas-button-primary" onClick={() => decide(true)} disabled={saving || selected.readiness_label !== "ready"}><Icon name="check" className="h-4 w-4" />Approve</button><button type="button" className="atlas-button atlas-button-danger" onClick={() => decide(false)} disabled={saving}><Icon name="close" className="h-4 w-4" />Reject</button></div>
                  </div>}
                  {selected.status === "ready" && selected.signed_off_at && <button type="button" className="atlas-button atlas-button-primary" onClick={publish} disabled={saving}><Icon name="release" className="h-4 w-4" />Publish and lock</button>}
                </div>
              )}
            </section>
          )}

          {releases.length >= 2 && <section className="atlas-panel mt-6">
            <div className="atlas-panel-heading"><div><p className="atlas-eyebrow">Release comparison</p><h2>Compare candidate evidence</h2><p>Review selection, readiness, and gate changes between two candidates.</p></div></div>
            <div className="atlas-release-compare-form"><select className="atlas-input" value={compareSource} onChange={(e) => setCompareSource(e.target.value)}><option value="">Source release</option>{releases.map((item) => <option key={item.id} value={item.id}>{item.version_label} — {item.name}</option>)}</select><select className="atlas-input" value={compareTarget} onChange={(e) => setCompareTarget(e.target.value)}><option value="">Target release</option>{releases.map((item) => <option key={item.id} value={item.id}>{item.version_label} — {item.name}</option>)}</select><button type="button" className="atlas-button atlas-button-primary" onClick={compare}><Icon name="compare" className="h-4 w-4" />Compare</button></div>
            {comparison && <div className="atlas-comparison-results"><div><span>Score change</span><strong>{comparison.readiness_score_change > 0 ? "+" : ""}{comparison.readiness_score_change}%</strong><small>{comparison.readiness_label_change}</small></div><div><span>Requirements</span><strong>+{comparison.requirements_added.length} / −{comparison.requirements_removed.length}</strong><small>added / removed</small></div><div><span>Test cases</span><strong>+{comparison.test_cases_added.length} / −{comparison.test_cases_removed.length}</strong><small>added / removed</small></div><div><span>Gate changes</span><strong>{comparison.gate_changes.length}</strong><small>changed evidence points</small></div></div>}
          </section>}
        </>
      )}
    </AppShell>
  );
}
