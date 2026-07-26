import { useEffect, useState } from "react";

import api from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { AdminBadge, AdminSection, formatBytes } from "../../components/AdminUI";
import Icon from "../../components/Icon";
import { Alert, LoadingState, StatCard } from "../../components/UI";
import { apiErrorMessage } from "../../utils/validation";

export default function AdminSystemPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      const response = await api.get("/admin/system");
      setData(response.data);
      setError("");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not read system health."));
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <AdminShell title="System health" description="Operational visibility without exposing database passwords, JWT keys, SMTP credentials, or other environment secrets." actions={<button type="button" onClick={load} className="atlas-button-secondary"><Icon name="refresh" className="h-4 w-4" />Refresh checks</button>}>
      {error && <Alert type="error">{error}</Alert>}
      {!data ? <LoadingState label="Checking ATLAS services..." /> : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Application" value={data.application_version} detail={`Alembic ${data.alembic_revision || "unknown"}`} icon="atlas" tone="indigo" />
            <StatCard label="Storage" value={formatBytes(data.storage_usage_bytes)} detail="Uploads, vectors, and model cache" icon="server" tone="violet" />
            <StatCard label="AI indexes" value={`${data.ready_ai_index_count}/${data.total_ai_index_count}`} detail="Ready project knowledge indexes" icon="assistant" tone="emerald" />
            <StatCard label="Critical events" value={data.recent_critical_event_count} detail="Recorded since start of today" icon="alert" tone="cyan" />
          </div>

          <AdminSection title="Service checks" description="Checks are performed by the backend at request time.">
            <div className="grid gap-4 md:grid-cols-2">{data.services.map((service) => (
              <article key={service.key} className="admin-service-card">
                <div className="flex items-start justify-between gap-3"><span className="admin-service-icon"><Icon name={service.key === "ai" ? "assistant" : service.key === "email" ? "send" : service.key === "database" ? "server" : "shield"} className="h-5 w-5" /></span><AdminBadge value={service.status} /></div>
                <h3>{service.label}</h3><p>{service.message}</p>
              </article>
            ))}</div>
          </AdminSection>

          <div className="grid gap-6 xl:grid-cols-2">
            <AdminSection title="Storage allocation" description="Read-only totals from configured ATLAS storage directories.">
              <dl className="admin-detail-grid"><div><dt>Document uploads</dt><dd>{formatBytes(data.upload_storage_bytes)}</dd></div><div><dt>Vector index</dt><dd>{formatBytes(data.vector_storage_bytes)}</dd></div><div><dt>Model cache</dt><dd>{formatBytes(data.model_storage_bytes)}</dd></div><div><dt>Total</dt><dd>{formatBytes(data.storage_usage_bytes)}</dd></div></dl>
            </AdminSection>
            <AdminSection title="Operational attention" description="Counts that may require administrator follow-up.">
              <dl className="admin-detail-grid"><div><dt>Failed document processing</dt><dd>{data.failed_document_count}</dd></div><div><dt>Database</dt><dd><AdminBadge value={data.database_status} /></dd></div><div><dt>Migration revision</dt><dd>{data.alembic_revision || "Unavailable"}</dd></div><div><dt>Secrets displayed</dt><dd>None</dd></div></dl>
            </AdminSection>
          </div>
        </div>
      )}
    </AdminShell>
  );
}
