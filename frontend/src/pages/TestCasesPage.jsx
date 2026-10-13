import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client";
import AppShell from "../components/AppShell";
import Icon from "../components/Icon";
import ProjectNav from "../components/ProjectNav";
import { Alert, EmptyState, LoadingState } from "../components/UI";

const blankStep = () => ({ action: "", expected_result: "" });
const blankForm = {
  requirement_id: "",
  title: "",
  objective: "",
  preconditions: "",
  test_data: "",
  overall_expected_result: "",
  test_type: "functional",
  priority: "medium",
  status: "draft",
  source: "manual",
  generation_explanation: "",
  reviewer_name: "",
  review_comments: "",
  rejection_reason: "",
  steps: [blankStep()],
};


function TestMetric({ label, value, detail }) {
  return (
    <div className="atlas-metric-card">
      <p className="atlas-metric-label">{label}</p>
      <p className="atlas-metric-value">{value}</p>
      {detail && <p className="atlas-metric-detail">{detail}</p>}
    </div>
  );
}

export default function TestCasesPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [items, setItems] = useState([]);
  const [requirements, setRequirements] = useState([]);
  const [summary, setSummary] = useState(null);
  const [form, setForm] = useState(blankForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [generateRequirement, setGenerateRequirement] = useState("");
  const [generateType, setGenerateType] = useState("functional");

  const load = async () => {
    setLoading(true);
    try {
      const [projectResponse, casesResponse, requirementsResponse, summaryResponse] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/test-cases`),
        api.get(`/projects/${projectId}/requirements`),
        api.get(`/projects/${projectId}/test-cases/summary`),
      ]);
      setProject(projectResponse.data);
      setItems(casesResponse.data);
      setRequirements(requirementsResponse.data);
      setSummary(summaryResponse.data);
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to load test case intelligence." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [projectId]);

  const filtered = useMemo(() => items.filter((item) => {
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || `${item.code} ${item.title} ${item.objective}`.toLowerCase().includes(query);
    const matchesStatus = !statusFilter || item.status === statusFilter;
    return matchesSearch && matchesStatus;
  }), [items, search, statusFilter]);

  const updateStep = (index, key, value) => {
    setForm((current) => ({ ...current, steps: current.steps.map((step, i) => i === index ? { ...step, [key]: value } : step) }));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!form.title.trim() || !form.objective.trim() || !form.overall_expected_result.trim()) {
      setMessage({ type: "error", text: "Title, objective, and overall expected result are required." });
      return;
    }
    if (form.steps.some((step) => !step.action.trim() || !step.expected_result.trim())) {
      setMessage({ type: "error", text: "Every test step needs an action and expected result." });
      return;
    }
    if (form.status === "rejected" && !form.rejection_reason.trim()) {
      setMessage({ type: "error", text: "A rejection reason is required." });
      return;
    }
    setSaving(true);
    try {
      const payload = { ...form, requirement_id: form.requirement_id || null };
      if (editingId) {
        await api.put(`/projects/${projectId}/test-cases/${editingId}`, { ...payload, change_note: "Updated through Test Case Intelligence workspace" });
      } else {
        await api.post(`/projects/${projectId}/test-cases`, payload);
      }
      setForm(blankForm);
      setEditingId(null);
      setMessage({ type: "success", text: editingId ? "Test case updated and versioned." : "Test case created." });
      await load();
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Unable to save test case." });
    } finally {
      setSaving(false);
    }
  };

  const edit = (item) => {
    setEditingId(item.id);
    setForm({
      requirement_id: item.requirement_id || "",
      title: item.title,
      objective: item.objective,
      preconditions: item.preconditions || "",
      test_data: item.test_data || "",
      overall_expected_result: item.overall_expected_result,
      test_type: item.test_type,
      priority: item.priority,
      status: item.status,
      source: item.source,
      generation_explanation: item.generation_explanation || "",
      reviewer_name: item.reviewer_name || "",
      review_comments: item.review_comments || "",
      rejection_reason: item.rejection_reason || "",
      steps: item.steps.map(({ action, expected_result }) => ({ action, expected_result })),
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this test case and its version history?")) return;
    await api.delete(`/projects/${projectId}/test-cases/${id}`);
    setMessage({ type: "success", text: "Test case deleted." });
    await load();
  };

  const generate = async () => {
    if (!generateRequirement || !generateType) {
      setMessage({ type: "error", text: "Select an approved/reviewed requirement and exactly one test type." });
      return;
    }
    setSaving(true);
    try {
      await api.post(`/projects/${projectId}/test-cases/generate`, { requirement_id: generateRequirement, test_type: generateType });
      setMessage({ type: "success", text: "AI-assisted draft test cases generated with requirement traceability." });
      await load();
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Generation failed." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell>
      <ProjectNav projectId={projectId} />
      <section className="atlas-page-header atlas-test-case-header">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-indigo-600">
            Test case workspace
          </p>
          <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">
            {project?.name || "Test Case Intelligence"}
          </h1>
          <p className="mt-4 max-w-3xl leading-7 text-slate-600">
            Create, generate, review, version, and trace test cases back to project requirements.
          </p>
        </div>
        <div className="atlas-header-metrics">
          <TestMetric label="Total test cases" value={summary?.total || 0} />
          <TestMetric label="Approved" value={summary?.approved || 0} />
          <TestMetric label="Needs review" value={summary?.needs_review || 0} />
          <TestMetric
            label="Requirement coverage"
            value={`${summary?.coverage_percent || 0}%`}
            detail={`${summary?.covered_requirements || 0} of ${summary?.requirement_count || 0}`}
          />
        </div>
      </section>
      {message && <div className="mb-5"><Alert type={message.type} onClose={() => setMessage(null)}>{message.text}</Alert></div>}
      {loading ? <LoadingState label="Loading test intelligence..." /> : <>
        <div className="atlas-test-workspace mb-6">
        <aside className="atlas-panel atlas-test-generator">
          <div className="atlas-panel-heading"><div><p className="atlas-eyebrow">AI-assisted generation</p><h2>Generate traced scenarios</h2><p>Create draft scenarios from an approved or reviewed requirement.</p></div></div>
          <div className="grid gap-4 lg:grid-cols-[1fr_2fr_auto]">
            <select className="atlas-input" value={generateRequirement} onChange={(e) => setGenerateRequirement(e.target.value)}>
              <option value="">Select approved/reviewed requirement</option>
              {requirements.filter((r) => ["approved", "reviewed"].includes(r.status)).map((r) => <option key={r.id} value={r.id}>{r.code} — {r.title}</option>)}
            </select>
            <label className="atlas-field">
              <span>Test type <small className="font-normal text-slate-400">(select exactly one)</small></span>
              <select className="atlas-input" value={generateType} onChange={(e) => setGenerateType(e.target.value)}>
                {["functional","positive","negative","boundary","security","performance","integration","regression"].map((type) => <option key={type} value={type}>{type.replace("_", " ")}</option>)}
              </select>
            </label>
            <button className="atlas-button atlas-button-primary" type="button" onClick={generate} disabled={saving}><Icon name="assistant" className="h-4 w-4" />Generate</button>
          </div>
        </aside>

        <section id="test-case-authoring" className="atlas-panel atlas-test-authoring">
          <div className="atlas-panel-heading"><div><p className="atlas-eyebrow">{editingId ? "Version update" : "Manual authoring"}</p><h2>{editingId ? "Edit test case" : "Create test case"}</h2><p>{editingId ? "Update the selected test case and preserve its version history." : "Author a complete, traceable test case with clear steps and expected outcomes."}</p></div></div>
          <form onSubmit={submit} className="grid gap-4">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="atlas-field"><span>Source requirement</span><select className="atlas-input" value={form.requirement_id} onChange={(e) => setForm({ ...form, requirement_id: e.target.value })}><option value="">Unlinked/manual</option>{requirements.map((r) => <option key={r.id} value={r.id}>{r.code} — {r.title}</option>)}</select></label>
              <label className="atlas-field"><span>Title</span><input className="atlas-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} maxLength={200} /></label>
            </div>
            <label className="atlas-field"><span>Objective</span><textarea className="atlas-input" rows="3" value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })} /></label>
            <div className="grid gap-4 md:grid-cols-2"><label className="atlas-field"><span>Preconditions</span><textarea className="atlas-input" rows="3" value={form.preconditions} onChange={(e) => setForm({ ...form, preconditions: e.target.value })} /></label><label className="atlas-field"><span>Test data</span><textarea className="atlas-input" rows="3" value={form.test_data} onChange={(e) => setForm({ ...form, test_data: e.target.value })} /></label></div>
            <div className="grid gap-4 md:grid-cols-4">
              <label className="atlas-field"><span>Type</span><select className="atlas-input" value={form.test_type} onChange={(e) => setForm({ ...form, test_type: e.target.value })}>{["functional","positive","negative","boundary","security","performance","integration","regression"].map((x) => <option key={x}>{x}</option>)}</select></label>
              <label className="atlas-field"><span>Priority</span><select className="atlas-input" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>{["low","medium","high","critical"].map((x) => <option key={x}>{x}</option>)}</select></label>
              <label className="atlas-field"><span>Status</span><select className="atlas-input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>{["draft","in_review","approved","rejected","needs_review","archived"].map((x) => <option key={x} value={x}>{x.replace("_", " ")}</option>)}</select></label>
              <label className="atlas-field"><span>Reviewer</span><input className="atlas-input" value={form.reviewer_name} onChange={(e) => setForm({ ...form, reviewer_name: e.target.value })} /></label>
            </div>
            <div className="atlas-step-builder"><div className="flex items-center justify-between"><h3>Numbered test steps</h3><button className="atlas-button atlas-button-secondary" type="button" onClick={() => setForm({ ...form, steps: [...form.steps, blankStep()] })}><Icon name="plus" className="h-4 w-4" />Add step</button></div>{form.steps.map((step, index) => <div className="atlas-step-row" key={index}><strong>{index + 1}</strong><input className="atlas-input" placeholder="Action" value={step.action} onChange={(e) => updateStep(index,"action",e.target.value)} /><input className="atlas-input" placeholder="Expected result" value={step.expected_result} onChange={(e) => updateStep(index,"expected_result",e.target.value)} /><button type="button" className="atlas-icon-button" disabled={form.steps.length === 1} onClick={() => setForm({ ...form, steps: form.steps.filter((_,i) => i !== index) })}><Icon name="trash" className="h-4 w-4" /></button></div>)}</div>
            <label className="atlas-field"><span>Overall expected result</span><textarea className="atlas-input" rows="3" value={form.overall_expected_result} onChange={(e) => setForm({ ...form, overall_expected_result: e.target.value })} /></label>
            <div className="grid gap-4 md:grid-cols-2"><label className="atlas-field"><span>Review comments</span><textarea className="atlas-input" rows="2" value={form.review_comments} onChange={(e) => setForm({ ...form, review_comments: e.target.value })} /></label><label className="atlas-field"><span>Rejection reason</span><textarea className="atlas-input" rows="2" value={form.rejection_reason} onChange={(e) => setForm({ ...form, rejection_reason: e.target.value })} /></label></div>
            <div className="flex gap-3"><button className="atlas-button atlas-button-primary" disabled={saving}>{saving ? "Saving..." : editingId ? "Save new version" : "Create test case"}</button>{editingId && <button type="button" className="atlas-button atlas-button-secondary" onClick={() => { setEditingId(null); setForm(blankForm); }}>Cancel</button>}</div>
          </form>
        </section>
        </div>

        <section className="atlas-panel atlas-test-repository">
          <div className="atlas-panel-heading atlas-test-repository-heading"><div><p className="atlas-eyebrow">Test repository</p><h2>Traceable test cases</h2><p>Search, review, edit, and maintain every test case connected to this project.</p></div><div className="atlas-test-filters"><input className="atlas-input" placeholder="Search code, title, objective" value={search} onChange={(e) => setSearch(e.target.value)} /><select className="atlas-input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All statuses</option>{["draft","in_review","approved","rejected","needs_review","archived"].map((x) => <option key={x}>{x}</option>)}</select></div></div>
          {filtered.length === 0 ? <EmptyState icon="test" title="No test cases found" description="Create a manual test case or generate scenarios from an approved requirement." /> : <div className="grid gap-4">{filtered.map((item) => <article className="atlas-test-card" key={item.id}><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex flex-wrap gap-2"><span className="atlas-badge">{item.code}</span><span className="atlas-badge">{item.test_type}</span><span className="atlas-badge">{item.priority}</span><span className="atlas-badge">{item.status.replace("_"," ")}</span><span className="atlas-badge">v{item.version}</span></div><h3>{item.title}</h3><p>{item.objective}</p></div><div className="flex gap-2"><button className="atlas-icon-button" onClick={() => edit(item)}><Icon name="edit" className="h-4 w-4" /></button><button className="atlas-icon-button" onClick={() => remove(item.id)}><Icon name="trash" className="h-4 w-4" /></button></div></div><ol className="mt-4 grid gap-2">{item.steps.map((step) => <li key={step.id}><strong>{step.position}. {step.action}</strong><span>Expected: {step.expected_result}</span></li>)}</ol>{item.generation_explanation && <p className="atlas-muted mt-3">{item.generation_explanation}</p>}</article>)}</div>}
        </section>
      </>}
    </AppShell>
  );
}
