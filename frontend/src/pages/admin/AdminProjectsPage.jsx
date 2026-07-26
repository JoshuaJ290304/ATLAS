import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { AdminBadge, AdminSection, AdminTable, formatDate } from "../../components/AdminUI";
import Icon from "../../components/Icon";
import { Alert, EmptyState, LoadingState } from "../../components/UI";
import { apiErrorMessage } from "../../utils/validation";

export default function AdminProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [transferOwner, setTransferOwner] = useState({});
  const [transferReason, setTransferReason] = useState({});
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [projectResponse, userResponse] = await Promise.all([
        api.get("/admin/projects", { params: { search: search.trim() || undefined, project_status: status || undefined } }),
        api.get("/admin/users", { params: { account_status: "active" } }),
      ]);
      setProjects(projectResponse.data);
      setUsers(userResponse.data);
      setError("");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load platform projects."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [status]);

  const totals = useMemo(() => ({
    active: projects.filter((project) => project.status === "active").length,
    failed: projects.reduce((sum, project) => sum + project.failed_document_count, 0),
    risks: projects.reduce((sum, project) => sum + project.high_risk_impact_count, 0),
  }), [projects]);

  async function changeStatus(project) {
    setBusyId(project.id);
    setError("");
    try {
      const nextStatus = project.status === "active" ? "archived" : "active";
      await api.patch(`/admin/projects/${project.id}/status`, { status: nextStatus, reason: `Administrative ${nextStatus} action` });
      setNotice(`Project ${nextStatus === "archived" ? "archived" : "restored"} successfully.`);
      await load();
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not update project status."));
    } finally {
      setBusyId("");
    }
  }

  async function transfer(project) {
    const newOwnerId = transferOwner[project.id];
    const reason = (transferReason[project.id] || "").trim();
    if (!newOwnerId || !reason) {
      setError("Select an active user and enter a transfer reason.");
      return;
    }
    setBusyId(project.id);
    setError("");
    try {
      await api.post(`/admin/projects/${project.id}/transfer`, { new_owner_id: newOwnerId, reason });
      setNotice(`Ownership of “${project.name}” was transferred.`);
      setTransferOwner((current) => ({ ...current, [project.id]: "" }));
      setTransferReason((current) => ({ ...current, [project.id]: "" }));
      await load();
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not transfer project ownership."));
    } finally {
      setBusyId("");
    }
  }

  function submit(event) { event.preventDefault(); load(); }

  return (
    <AdminShell title="Project oversight" description="Inspect every ATLAS project, its real owner and artifact counts, then archive, restore, or transfer ownership with an audit trail." actions={<button type="button" onClick={load} className="atlas-button-secondary"><Icon name="refresh" className="h-4 w-4" />Refresh</button>}>
      {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}
      {notice && <Alert type="success" onClose={() => setNotice("")}>{notice}</Alert>}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="admin-mini-stat"><span>Visible projects</span><strong>{projects.length}</strong></div>
        <div className="admin-mini-stat"><span>Active projects</span><strong>{totals.active}</strong></div>
        <div className="admin-mini-stat"><span>Operational alerts</span><strong>{totals.failed + totals.risks}</strong></div>
      </div>

      <AdminSection title="All projects" description="Search by project name, owner name, or owner email." className="mt-6">
        <form onSubmit={submit} className="admin-filter-bar">
          <label className="relative flex-1"><Icon name="search" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input className="atlas-input !mt-0 !pl-10" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search projects or owners" /></label>
          <select className="atlas-select !mt-0" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All statuses</option><option value="active">Active</option><option value="archived">Archived</option></select>
          <button className="atlas-button-primary" type="submit"><Icon name="search" className="h-4 w-4" />Search</button>
        </form>

        {loading ? <LoadingState label="Loading platform projects..." /> : projects.length === 0 ? <EmptyState icon="home" title="No matching projects" description="Adjust the search or status filter." /> : (
          <AdminTable>
            <thead><tr><th>Project</th><th>Owner</th><th>Status</th><th>Artifacts</th><th>Alerts</th><th>Updated</th><th>Operations</th></tr></thead>
            <tbody>{projects.map((project) => (
              <tr key={project.id}>
                <td><span className="admin-table-link">{project.name}<small>{project.description || "No description"}</small></span></td>
                <td><Link to={`/admin/users/${project.owner_id}`} className="admin-table-link">{project.owner_name}<small>{project.owner_email}</small></Link></td>
                <td><AdminBadge value={project.status} /></td>
                <td><span className="admin-artifact-count">{project.document_count} docs · {project.requirement_count} reqs · {project.test_case_count} tests · {project.release_candidate_count} releases</span></td>
                <td>{project.failed_document_count || project.high_risk_impact_count ? <span className="text-xs font-black text-rose-600">{project.failed_document_count} failed docs · {project.high_risk_impact_count} high-risk impacts</span> : <span className="text-xs font-bold text-emerald-600">No current alerts</span>}</td>
                <td>{formatDate(project.updated_at)}</td>
                <td>
                  <div className="admin-project-actions">
                    <button type="button" disabled={busyId === project.id} onClick={() => changeStatus(project)} className="atlas-button-secondary !px-3 !py-2">{project.status === "active" ? "Archive" : "Restore"}</button>
                    <select value={transferOwner[project.id] || ""} onChange={(event) => setTransferOwner((current) => ({ ...current, [project.id]: event.target.value }))} className="atlas-select !mt-0 !py-2" aria-label={`New owner for ${project.name}`}><option value="">New owner</option>{users.filter((user) => user.id !== project.owner_id).map((user) => <option key={user.id} value={user.id}>{user.name} ({user.email})</option>)}</select>
                    <input value={transferReason[project.id] || ""} onChange={(event) => setTransferReason((current) => ({ ...current, [project.id]: event.target.value }))} className="atlas-input !mt-0 !py-2" placeholder="Transfer reason" maxLength={1000} />
                    <button type="button" disabled={busyId === project.id} onClick={() => transfer(project)} className="atlas-button-secondary !px-3 !py-2">Transfer</button>
                  </div>
                </td>
              </tr>
            ))}</tbody>
          </AdminTable>
        )}
      </AdminSection>
    </AdminShell>
  );
}
