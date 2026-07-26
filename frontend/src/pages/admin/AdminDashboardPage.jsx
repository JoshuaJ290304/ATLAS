import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { AdminBadge, AdminSection, AdminTable, formatDate } from "../../components/AdminUI";
import Icon from "../../components/Icon";
import { Alert, LoadingState, StatCard } from "../../components/UI";
import { apiErrorMessage } from "../../utils/validation";

export default function AdminDashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      const response = await api.get("/admin/dashboard");
      setData(response.data);
      setError("");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load the administration dashboard."));
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <AdminShell
      title="Platform overview"
      description="Monitor every existing ATLAS user, project, quality artifact, and administrative action from one protected workspace."
      actions={<button type="button" onClick={load} className="atlas-button-secondary"><Icon name="refresh" className="h-4 w-4" />Refresh</button>}
    >
      {error && <Alert type="error">{error}</Alert>}
      {!data ? <LoadingState label="Loading platform overview..." /> : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Users" value={data.total_users} detail={`${data.active_users} active · ${data.suspended_users} suspended`} icon="users" tone="indigo" />
            <StatCard label="Administrators" value={data.administrators} detail="Protected platform operators" icon="shield" tone="violet" />
            <StatCard label="Projects" value={data.total_projects} detail={`${data.active_projects} active · ${data.archived_projects} archived`} icon="home" tone="emerald" />
            <StatCard label="Release candidates" value={data.total_release_candidates} detail="Across all projects" icon="release" tone="cyan" />
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Documents" value={data.total_documents} detail={`${data.processed_documents} processed · ${data.failed_documents} failed`} icon="document" tone="indigo" />
            <StatCard label="Requirements" value={data.total_requirements} detail="Platform-wide engineering evidence" icon="requirement" tone="violet" />
            <StatCard label="Test cases" value={data.total_test_cases} detail="Manual and AI-assisted tests" icon="test" tone="emerald" />
            <StatCard label="Operations" value="Audited" detail="Role, security, and ownership changes" icon="history" tone="cyan" />
          </div>

          <div className="grid gap-6 2xl:grid-cols-2">
            <AdminSection
              title="Recent registrations"
              description="These are real records from the existing users table."
              actions={<Link to="/admin/users" className="atlas-button-secondary">Manage users<Icon name="arrowRight" className="h-4 w-4" /></Link>}
            >
              <AdminTable>
                <thead><tr><th>User</th><th>Role</th><th>Status</th><th>Projects</th><th>Joined</th></tr></thead>
                <tbody>
                  {data.recent_registrations.map((user) => (
                    <tr key={user.id}>
                      <td><Link to={`/admin/users/${user.id}`} className="admin-table-link">{user.name}<small>{user.email}</small></Link></td>
                      <td><AdminBadge value={user.role} /></td>
                      <td><AdminBadge value={user.account_status} /></td>
                      <td>{user.project_count}</td>
                      <td>{formatDate(user.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </AdminTable>
            </AdminSection>

            <AdminSection
              title="Recent administrative activity"
              description="Authentication and platform-control events are recorded automatically."
              actions={<Link to="/admin/audit" className="atlas-button-secondary">Open audit log<Icon name="arrowRight" className="h-4 w-4" /></Link>}
            >
              {data.recent_actions.length === 0 ? <p className="text-sm text-slate-500">No platform audit events have been recorded yet.</p> : (
                <div className="space-y-3">
                  {data.recent_actions.map((event) => (
                    <div key={event.id} className="admin-activity-row">
                      <span className="admin-activity-icon"><Icon name="history" className="h-4 w-4" /></span>
                      <div className="min-w-0 flex-1"><p>{event.action.replaceAll("_", " ").replaceAll(".", " · ")}</p><span>{event.actor_name || "System"} · {formatDate(event.created_at, true)}</span></div>
                      <AdminBadge value={event.severity} />
                    </div>
                  ))}
                </div>
              )}
            </AdminSection>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Link to="/admin/users" className="admin-command-card"><Icon name="users" /><div><strong>User management</strong><p>Review existing accounts, roles, activity, and project ownership.</p></div></Link>
            <Link to="/admin/projects" className="admin-command-card"><Icon name="home" /><div><strong>Project oversight</strong><p>Archive, restore, inspect, or transfer any project safely.</p></div></Link>
            <Link to="/admin/system" className="admin-command-card"><Icon name="server" /><div><strong>System operations</strong><p>Check database, email, AI, migration, and storage health.</p></div></Link>
          </div>
        </div>
      )}
    </AdminShell>
  );
}
