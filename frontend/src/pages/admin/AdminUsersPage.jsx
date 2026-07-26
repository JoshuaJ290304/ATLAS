import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { AdminBadge, AdminSection, AdminTable, formatDate } from "../../components/AdminUI";
import Icon from "../../components/Icon";
import { Alert, EmptyState, LoadingState } from "../../components/UI";
import { apiErrorMessage } from "../../utils/validation";

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const response = await api.get("/admin/users", {
        params: {
          search: search.trim() || undefined,
          role: role || undefined,
          account_status: status || undefined,
        },
      });
      setUsers(response.data);
      setError("");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load existing users."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [role, status]);

  const totals = useMemo(() => ({
    active: users.filter((user) => user.is_active).length,
    admins: users.filter((user) => user.role === "admin").length,
    projects: users.reduce((sum, user) => sum + user.project_count, 0),
  }), [users]);

  function submitSearch(event) {
    event.preventDefault();
    load();
  }

  return (
    <AdminShell
      title="Existing users"
      description="Manage the real ATLAS accounts already stored in the database. Password hashes and reset tokens are never exposed."
      actions={<button type="button" onClick={load} className="atlas-button-secondary"><Icon name="refresh" className="h-4 w-4" />Refresh</button>}
    >
      {error && <Alert type="error">{error}</Alert>}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="admin-mini-stat"><span>Visible users</span><strong>{users.length}</strong></div>
        <div className="admin-mini-stat"><span>Active accounts</span><strong>{totals.active}</strong></div>
        <div className="admin-mini-stat"><span>Owned projects</span><strong>{totals.projects}</strong></div>
      </div>

      <AdminSection title="User directory" description="Search by name or email and filter by role or account status." className="mt-6">
        <form onSubmit={submitSearch} className="admin-filter-bar admin-filter-bar-users">
          <label className="admin-filter-search">
            <Icon name="search" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input className="atlas-input !mt-0 !pl-10" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search existing users" />
          </label>
          <select className="atlas-select !mt-0 admin-filter-control" value={role} onChange={(event) => setRole(event.target.value)} aria-label="Filter role">
            <option value="">All roles</option><option value="admin">Administrators</option><option value="user">Users</option>
          </select>
          <select className="atlas-select !mt-0 admin-filter-control" value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filter status">
            <option value="">All statuses</option><option value="active">Active</option><option value="suspended">Suspended</option>
          </select>
          <button className="atlas-button-primary admin-filter-submit" type="submit"><Icon name="search" className="h-4 w-4" />Search</button>
        </form>

        {loading ? <LoadingState label="Loading existing users..." /> : users.length === 0 ? (
          <EmptyState icon="users" title="No matching users" description="Adjust the search or account filters." />
        ) : (
          <AdminTable className="admin-table-users" label="Existing ATLAS users">
            <thead><tr><th>User</th><th>Role</th><th>Status</th><th>Last login</th><th>Projects</th><th>Artifacts</th><th /></tr></thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td><Link className="admin-table-link" to={`/admin/users/${user.id}`}>{user.name}<small>{user.email}</small></Link></td>
                  <td><AdminBadge value={user.role} /></td>
                  <td><AdminBadge value={user.account_status} /></td>
                  <td className="admin-cell-nowrap">{formatDate(user.last_login_at, true)}</td>
                  <td className="admin-cell-number">{user.project_count}</td>
                  <td className="admin-cell-artifacts"><span className="admin-artifact-count">{user.document_count} docs · {user.requirement_count} reqs · {user.test_case_count} tests</span></td>
                  <td className="admin-cell-action"><Link to={`/admin/users/${user.id}`} className="atlas-button-secondary admin-row-action !px-3 !py-2">View<Icon name="arrowRight" className="h-4 w-4" /></Link></td>
                </tr>
              ))}
            </tbody>
          </AdminTable>
        )}
      </AdminSection>
    </AdminShell>
  );
}
