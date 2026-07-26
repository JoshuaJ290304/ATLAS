import { useEffect, useState } from "react";

import api from "../../api/client";
import AdminShell from "../../components/AdminShell";
import { AdminSection } from "../../components/AdminUI";
import Icon from "../../components/Icon";
import { Alert, LoadingState } from "../../components/UI";
import { apiErrorMessage } from "../../utils/validation";

export default function AdminSettingsPage() {
  const [form, setForm] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      const response = await api.get("/admin/settings");
      setForm({ ...response.data, allowed_document_extensions: response.data.allowed_document_extensions.join(", ") });
      setError("");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not load platform settings."));
    }
  }

  useEffect(() => { load(); }, []);

  async function save(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const payload = {
        registration_enabled: form.registration_enabled,
        maintenance_mode: form.maintenance_mode,
        maintenance_message: form.maintenance_message?.trim() || null,
        ai_generation_enabled: form.ai_generation_enabled,
        session_duration_minutes: Number(form.session_duration_minutes),
        password_reset_expiry_minutes: Number(form.password_reset_expiry_minutes),
        max_upload_size_mb: Number(form.max_upload_size_mb),
        allowed_document_extensions: form.allowed_document_extensions.split(",").map((value) => value.trim()).filter(Boolean),
      };
      const response = await api.put("/admin/settings", payload);
      setForm({ ...response.data, allowed_document_extensions: response.data.allowed_document_extensions.join(", ") });
      setNotice("Platform settings saved and recorded in the audit log.");
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not save platform settings."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <AdminShell title="Platform settings" description="Safe operational controls are persisted in PostgreSQL. Security secrets remain environment variables and are never shown here." actions={<button type="button" onClick={load} className="atlas-button-secondary"><Icon name="refresh" className="h-4 w-4" />Reload</button>}>
      {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}
      {notice && <Alert type="success" onClose={() => setNotice("")}>{notice}</Alert>}
      {!form ? <LoadingState label="Loading platform settings..." /> : (
        <form onSubmit={save} className="space-y-6">
          <AdminSection title="Access and maintenance" description="These settings take effect immediately for subsequent requests.">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="admin-toggle-card"><input type="checkbox" checked={form.registration_enabled} onChange={(event) => setForm({ ...form, registration_enabled: event.target.checked })} /><span><strong>Allow new registrations</strong><small>When disabled, the public registration endpoint returns 403.</small></span></label>
              <label className="admin-toggle-card"><input type="checkbox" checked={form.maintenance_mode} onChange={(event) => setForm({ ...form, maintenance_mode: event.target.checked })} /><span><strong>Maintenance mode</strong><small>Non-administrators receive a maintenance response on protected API requests.</small></span></label>
              <label className="admin-toggle-card"><input type="checkbox" checked={form.ai_generation_enabled} onChange={(event) => setForm({ ...form, ai_generation_enabled: event.target.checked })} /><span><strong>AI operations enabled</strong><small>Controls assistant indexing, semantic search, and grounded question answering.</small></span></label>
              <label className="atlas-label">Maintenance message<textarea className="atlas-textarea" rows={3} value={form.maintenance_message || ""} onChange={(event) => setForm({ ...form, maintenance_message: event.target.value })} maxLength={1000} placeholder="ATLAS is temporarily unavailable while maintenance is completed." /></label>
            </div>
          </AdminSection>

          <AdminSection title="Security and session policy" description="Changing session duration affects newly issued tokens. Invalidating a user session remains available in User Management.">
            <div className="grid gap-5 md:grid-cols-2">
              <label className="atlas-label">Session duration (minutes)<input type="number" min="5" max="10080" className="atlas-input" value={form.session_duration_minutes} onChange={(event) => setForm({ ...form, session_duration_minutes: event.target.value })} /></label>
              <label className="atlas-label">Password-reset expiry (minutes)<input type="number" min="5" max="1440" className="atlas-input" value={form.password_reset_expiry_minutes} onChange={(event) => setForm({ ...form, password_reset_expiry_minutes: event.target.value })} /></label>
            </div>
          </AdminSection>

          <AdminSection title="Document upload policy" description="ATLAS currently supports secure PDF and DOCX processing. These values are enforced by the upload endpoint.">
            <div className="grid gap-5 md:grid-cols-2">
              <label className="atlas-label">Maximum upload size (MB)<input type="number" min="1" max="100" className="atlas-input" value={form.max_upload_size_mb} onChange={(event) => setForm({ ...form, max_upload_size_mb: event.target.value })} /></label>
              <label className="atlas-label">Allowed extensions<input className="atlas-input" value={form.allowed_document_extensions} onChange={(event) => setForm({ ...form, allowed_document_extensions: event.target.value })} placeholder=".pdf, .docx" /><span className="atlas-help">Comma-separated. Supported values: .pdf and .docx.</span></label>
            </div>
          </AdminSection>

          <div className="flex justify-end"><button type="submit" disabled={saving} className="atlas-button-primary"><Icon name="check" className="h-4 w-4" />{saving ? "Saving settings..." : "Save platform settings"}</button></div>
        </form>
      )}
    </AdminShell>
  );
}
