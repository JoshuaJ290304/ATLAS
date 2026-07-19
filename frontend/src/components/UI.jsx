import Icon from "./Icon";

export function PageHeader({ eyebrow, title, description, actions, children }) {
  return (
    <section className="atlas-page-header">
      <div className="min-w-0">
        {eyebrow && <p className="atlas-eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="atlas-page-actions">{actions}</div>}
      {children}
    </section>
  );
}

export function StatCard({ label, value, detail, icon = "activity", tone = "indigo" }) {
  return (
    <div className={`atlas-stat atlas-stat-${tone}`}>
      <div className="atlas-stat-icon"><Icon name={icon} className="h-5 w-5" /></div>
      <div className="min-w-0">
        <p>{label}</p>
        <strong>{value}</strong>
        {detail && <span>{detail}</span>}
      </div>
    </div>
  );
}

export function Alert({ type = "info", children, onClose }) {
  const icon = type === "success" ? "check" : type === "error" ? "alert" : "info";
  return (
    <div className={`atlas-alert atlas-alert-${type}`} role={type === "error" ? "alert" : "status"}>
      <Icon name={icon} className="mt-0.5 h-5 w-5 shrink-0" />
      <div className="min-w-0 flex-1">{children}</div>
      {onClose && (
        <button type="button" onClick={onClose} aria-label="Dismiss message">
          <Icon name="close" className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

export function FieldError({ children }) {
  if (!children) return null;
  return <p className="atlas-field-error" role="alert">{children}</p>;
}

export function EmptyState({ icon = "document", title, description, action }) {
  return (
    <div className="atlas-empty-state">
      <div className="atlas-empty-icon"><Icon name={icon} className="h-7 w-7" /></div>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function LoadingState({ label = "Loading workspace..." }) {
  return (
    <div className="atlas-loading" role="status">
      <span className="atlas-spinner" />
      <span>{label}</span>
    </div>
  );
}

export function ProgressBar({ value, tone = "indigo", label }) {
  const normalized = Math.min(100, Math.max(0, Number(value) || 0));
  return (
    <div>
      {label && <div className="mb-2 flex items-center justify-between text-sm"><span>{label}</span><strong>{normalized.toFixed(1)}%</strong></div>}
      <div className="atlas-progress"><span className={`atlas-progress-${tone}`} style={{ width: `${normalized}%` }} /></div>
    </div>
  );
}
