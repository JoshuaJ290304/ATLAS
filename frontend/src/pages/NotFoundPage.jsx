import { Link } from "react-router-dom";

import AppShell from "../components/AppShell";
import Icon from "../components/Icon";

export default function NotFoundPage() {
  return (
    <AppShell>
      <section className="atlas-not-found">
        <span className="atlas-empty-icon"><Icon name="search" className="h-7 w-7" /></span>
        <p className="atlas-eyebrow">Page not found</p>
        <h1>We could not find that workspace.</h1>
        <p>The address may be outdated, or the project resource may have been removed.</p>
        <Link to="/" className="atlas-button-primary mt-6">
          <Icon name="home" className="h-4 w-4" /> Return to projects
        </Link>
      </section>
    </AppShell>
  );
}
