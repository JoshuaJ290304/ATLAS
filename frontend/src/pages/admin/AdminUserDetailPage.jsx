import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import api from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { AdminBadge, AdminSection, AdminTable, formatDate } from "../../components/AdminUI";
import Icon from "../../components/Icon";
import { Alert, LoadingState, StatCard } from "../../components/UI";
import { apiErrorMessage } from "../../utils/validation";

export default function AdminUserDetailPage() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const response = await api.get(`/admin/users/${userId}`);
      setUser(response.data);
      setError("");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load this user."));
    }
  }

  useEffect(() => { load(); }, [userId]);

  async function action(request, successMessage) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await request();
      setNotice(successMessage);
      await load();
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "The administrative action could not be completed."));
    } finally {
      setBusy(false);
    }
  }

  if (!user && !error) return <AdminShell title="User details" description="Loading existing account data."><LoadingState label="Loading user details..." /></AdminShell>;

  return (
    <AdminShell
      title={user?.name || "User details"}
      description={user ? `${user.email} · Existing ATLAS account created ${formatDate(user.created_at)}.` : "User record unavailable."}
      actions={<button type="button" onClick={() => navigate("/admin/users")} className="atlas-button-secondary"><Icon name="arrowLeft" className="h-4 w-4" />All users</button>}
    >
      {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}
      {notice && <Alert type="success" onClose={() => setNotice("")}>{notice}</Alert>}
      {user && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <StatCard label="Projects" value={user.project_count} detail="Owned workspaces" icon="home" tone="indigo" />
            <StatCard label="Documents" value={user.document_count} detail="Across owned projects" icon="document" tone="violet" />
            <StatCard label="Requirements" value={user.requirement_count} detail="Engineering records" icon="requirement" tone="emerald" />
            <StatCard label="Test cases" value={user.test_case_count} detail="Verification evidence" icon="test" tone="cyan" />
            <StatCard label="Releases" value={user.release_candidate_count} detail="Readiness candidates" icon="release" tone="indigo" />
          </div>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
            <AdminSection title="Account profile" description="Operational details from the existing users table.">
              <dl className="admin-detail-grid">
                <div><dt>User ID</dt><dd className="break-all">{user.id}</dd></div>
                <div><dt>Full name</dt><dd>{user.name}</dd></div>
                <div><dt>Email</dt><dd>{user.email}</dd></div>
                <div><dt>Role</dt><dd><AdminBadge value={user.role} /></dd></div>
                <div><dt>Account status</dt><dd><AdminBadge value={user.account_status} /></dd></div>
                <div><dt>Last login</dt><dd>{formatDate(user.last_login_at, true)}</dd></div>
                <div><dt>Registered</dt><dd>{formatDate(user.created_at, true)}</dd></div>
                <div><dt>Last updated</dt><dd>{formatDate(user.updated_at, true)}</dd></div>
                <div><dt>Session version</dt><dd>{user.session_version}</dd></div>
                <div><dt>Suspension reason</dt><dd>{user.suspension_reason || "Not suspended"}</dd></div>
              </dl>
            </AdminSection>

            <AdminSection title="Administrative controls" description="Every change invalidates affected sessions and is written to the platform audit log.">
              <label className="atlas-label">
                Administrative reason
                <textarea className="atlas-textarea" rows={3} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Reason for suspension or ownership/security action" maxLength={1000} />
              </label>
              <div className="mt-4 grid gap-3">
                <button
                  type="button"
                  disabled={busy}
                  className="atlas-button-secondary justify-center"
                  onClick={() => {
                    const demoting = user.role === "admin";
                    const message = demoting
                      ? `Demote ${user.name} to a regular user? Their administrator privileges will be removed.`
                      : `Promote ${user.name} to administrator? This grants platform administration privileges.`;
                    if (!window.confirm(message)) return;
                    action(
                      () => api.patch(`/admin/users/${user.id}/role`, { role: demoting ? "user" : "admin" }),
                      demoting ? "Administrator role removed." : "User promoted to administrator.",
                    );
                  }}
                ><Icon name="shield" className="h-4 w-4" />{user.role === "admin" ? "Demote to user" : "Promote to admin"}</button>
                <button
                  type="button"
                  disabled={busy}
                  className={user.is_active ? "atlas-button-danger justify-center" : "atlas-button-primary justify-center"}
                  onClick={() => {
                    const suspending = user.is_active;
                    if (suspending && !window.confirm(`Suspend ${user.name}? Their active sessions will be invalidated and they will be unable to authenticate.`)) return;
                    action(
                      () => api.patch(`/admin/users/${user.id}/status`, { status: suspending ? "suspended" : "active", reason: reason.trim() || null }),
                      suspending ? "Account suspended and sessions invalidated." : "Account reactivated.",
                    );
                  }}
                ><Icon name={user.is_active ? "lock" : "check"} className="h-4 w-4" />{user.is_active ? "Suspend account" : "Reactivate account"}</button>
                <button type="button" disabled={busy} className="atlas-button-secondary justify-center" onClick={() => action(() => api.post(`/admin/users/${user.id}/invalidate-sessions`), "All active sessions were invalidated.")}><Icon name="logout" className="h-4 w-4" />Invalidate all sessions</button>
                <button type="button" disabled={busy || !user.is_active} className="atlas-button-secondary justify-center" onClick={() => action(() => api.post(`/admin/users/${user.id}/password-reset`), "Password-recovery email requested.")}><Icon name="send" className="h-4 w-4" />Send password reset</button>
              </div>
            </AdminSection>
          </div>

          <AdminSection title="Owned projects" description="Projects and current artifact totals belonging to this existing user.">
            {user.projects.length === 0 ? <p className="text-sm text-slate-500">This user does not own any projects.</p> : (
              <AdminTable className="admin-table-user-projects" label="Projects owned by this user">
                <thead><tr><th>Project</th><th>Status</th><th>Documents</th><th>Requirements</th><th>Test cases</th><th>Releases</th><th>Updated</th></tr></thead>
                <tbody>{user.projects.map((project) => (
                  <tr key={project.id}><td><span className="admin-table-link">{project.name}<small>{project.id}</small></span></td><td><AdminBadge value={project.status} /></td><td>{project.document_count}</td><td>{project.requirement_count}</td><td>{project.test_case_count}</td><td>{project.release_candidate_count}</td><td>{formatDate(project.updated_at)}</td></tr>
                ))}</tbody>
              </AdminTable>
            )}
          </AdminSection>

          <AdminSection title="Recent account activity" description="Security and administration events associated with this user.">
            {user.recent_activity.length === 0 ? <p className="text-sm text-slate-500">No platform activity has been recorded for this account.</p> : (
              <div className="space-y-3">{user.recent_activity.map((event) => (
                <div key={event.id} className="admin-activity-row"><span className="admin-activity-icon"><Icon name="history" className="h-4 w-4" /></span><div className="min-w-0 flex-1"><p>{event.action.replaceAll(".", " · ").replaceAll("_", " ")}</p><span>{event.actor_name || "System"} · {formatDate(event.created_at, true)}</span></div><AdminBadge value={event.severity} /></div>
              ))}</div>
            )}
          </AdminSection>
        </div>
      )}
    </AdminShell>
  );
}
