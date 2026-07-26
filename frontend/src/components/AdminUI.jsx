export function AdminBadge({ value, tone }) {
  const normalized = String(value || "unknown").toLowerCase();
  const resolved = tone || (
    ["active", "healthy", "admin", "info"].includes(normalized) ? "success" :
    ["suspended", "critical", "failed", "unavailable"].includes(normalized) ? "danger" :
    ["warning", "archived"].includes(normalized) ? "warning" : "neutral"
  );
  return <span className={`admin-badge admin-badge-${resolved}`}>{String(value || "Unknown").replaceAll("_", " ")}</span>;
}

export function AdminSection({ title, description, actions, children, className = "" }) {
  return (
    <section className={`atlas-panel ${className}`}>
      <div className="flex flex-col gap-3 border-b border-slate-100 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div><h2 className="text-lg font-black text-slate-950">{title}</h2>{description && <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p>}</div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export function AdminTable({ children, className = "", label = "Administration data" }) {
  return (
    <div className="admin-table-wrap" tabIndex="0" role="region" aria-label={label}>
      <table className={`admin-table ${className}`.trim()}>{children}</table>
    </div>
  );
}

export function formatDate(value, includeTime = false) {
  if (!value) return "Never";
  return new Date(value).toLocaleString(undefined, includeTime ? undefined : { year: "numeric", month: "short", day: "numeric" });
}

export function formatBytes(value) {
  const bytes = Number(value || 0);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}
