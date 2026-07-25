import { Link, useLocation } from "react-router-dom";

import Icon from "./Icon";

const items = [
  { key: "documents", label: "Documents", icon: "document" },
  { key: "requirements", label: "Requirements", icon: "requirement" },
  { key: "traceability", label: "Traceability", icon: "trace" },
  { key: "test-cases", label: "Test Cases", icon: "test" },
  { key: "governance", label: "Reviews & Baselines", icon: "governance" },
  { key: "impact", label: "Impact", icon: "impact" },
  { key: "assistant", label: "AI Assistant", icon: "assistant" },
  { key: "analytics", label: "Analytics", icon: "analytics" },
];

export default function ProjectNav({ projectId }) {
  const location = useLocation();
  return (
    <div className="mb-7">
      <Link to="/" className="atlas-back-link">
        <Icon name="arrowLeft" className="h-4 w-4" /> All projects
      </Link>
      <nav aria-label="Project workspace modules" className="atlas-project-nav mt-4">
        {items.map((item) => {
          const to = `/projects/${projectId}/${item.key}`;
          const active = location.pathname === to;
          return (
            <Link
              key={item.key}
              to={to}
              className={active ? "is-active" : ""}
              aria-current={active ? "page" : undefined}
            >
              <Icon name={item.icon} className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
