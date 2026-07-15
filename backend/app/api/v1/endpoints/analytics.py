# ruff: noqa: E501
from __future__ import annotations

import csv
import html
import io
import json
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from app.api.dependencies import CurrentUser, DbSession
from app.api.v1.endpoints.projects import get_owned_project
from app.schemas.analytics import ProjectAnalyticsRead
from app.services.analytics import build_project_analytics

router = APIRouter(prefix="/projects/{project_id}/analytics", tags=["analytics"])


@router.get("", response_model=ProjectAnalyticsRead)
async def read_project_analytics(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ProjectAnalyticsRead:
    project = await get_owned_project(db, project_id, current_user.id)
    return await build_project_analytics(db, project)


@router.get("/export")
async def export_project_analytics(
    project_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    export_format: Literal["json", "csv", "html"] = Query(default="html", alias="format"),
) -> Response:
    project = await get_owned_project(db, project_id, current_user.id)
    analytics = await build_project_analytics(db, project)
    safe_name = "".join(character if character.isalnum() else "-" for character in project.name)
    safe_name = "-".join(filter(None, safe_name.split("-"))).lower() or "atlas-project"

    if export_format == "json":
        payload = json.dumps(analytics.model_dump(mode="json"), indent=2)
        return Response(
            content=payload,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}-analytics.json"'
            },
        )

    if export_format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "metric", "value"])
        rows = [
            ("project", "health_score", analytics.health.score),
            ("documents", "total", analytics.documents.total),
            ("documents", "extracted", analytics.documents.extracted),
            ("documents", "pages", analytics.documents.pages),
            ("requirements", "total", analytics.requirements.total),
            ("requirements", "functional", analytics.requirements.functional),
            ("requirements", "non_functional", analytics.requirements.non_functional),
            ("requirements", "ambiguous", analytics.requirements.ambiguous),
            ("traceability", "requirement_coverage_percent", analytics.traceability.requirement_coverage_percent),
            ("traceability", "artifact_coverage_percent", analytics.traceability.artifact_coverage_percent),
            ("traceability", "accepted_links", analytics.traceability.accepted),
            ("traceability", "suggested_links", analytics.traceability.suggested),
            ("traceability", "rejected_links", analytics.traceability.rejected),
            ("impact", "reports", analytics.impacts.total),
            ("impact", "average_risk_score", analytics.impacts.average_risk_score),
            ("assistant", "indexed_chunks", analytics.assistant.indexed_chunks),
            ("assistant", "conversations", analytics.assistant.conversations),
        ]
        writer.writerows(rows)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}-analytics.csv"'
            },
        )

    content = _render_html_report(analytics)
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}-project-report.html"'
        },
    )


def _render_html_report(analytics: ProjectAnalyticsRead) -> str:
    factor_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.label)}</td>"
        f"<td>{item.score:.1f}/{item.maximum:.0f}</td>"
        f"<td>{html.escape(item.explanation)}</td>"
        "</tr>"
        for item in analytics.health.factors
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(analytics.project_name)} · ATLAS Report</title>
<style>
body{{font-family:Inter,Arial,sans-serif;margin:0;background:#f8fafc;color:#0f172a}}
main{{max-width:980px;margin:40px auto;padding:0 24px}}
header{{padding:32px;border-radius:24px;background:linear-gradient(135deg,#312e81,#7c3aed);color:white}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}}
.card{{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:18px}}
.card strong{{display:block;font-size:28px;margin-top:6px}}
table{{width:100%;border-collapse:collapse;background:white;border-radius:16px;overflow:hidden}}
th,td{{padding:13px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}}
th{{background:#f1f5f9}}
@media(max-width:700px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body><main>
<header><p>ATLAS PROJECT HEALTH REPORT</p><h1>{html.escape(analytics.project_name)}</h1>
<p>Generated {analytics.generated_at.isoformat()}</p></header>
<section class="grid">
<div class="card">Health<strong>{analytics.health.score}/100</strong>{html.escape(analytics.health.label)}</div>
<div class="card">Requirements<strong>{analytics.requirements.total}</strong>{analytics.requirements.review_rate_percent:.1f}% reviewed</div>
<div class="card">Requirement coverage<strong>{analytics.traceability.requirement_coverage_percent:.1f}%</strong></div>
<div class="card">Average impact risk<strong>{analytics.impacts.average_risk_score:.1f}</strong></div>
</section>
<h2>Health factors</h2><table><thead><tr><th>Factor</th><th>Score</th><th>Explanation</th></tr></thead><tbody>{factor_rows}</tbody></table>
<h2>Project summary</h2><table><tbody>
<tr><th>Documents</th><td>{analytics.documents.total} total, {analytics.documents.extracted} extracted, {analytics.documents.pages} pages</td></tr>
<tr><th>Requirements</th><td>{analytics.requirements.functional} functional, {analytics.requirements.non_functional} non-functional, {analytics.requirements.ambiguous} ambiguous</td></tr>
<tr><th>Artifacts</th><td>{analytics.artifacts.total}</td></tr>
<tr><th>Trace links</th><td>{analytics.traceability.accepted} accepted, {analytics.traceability.suggested} suggested, {analytics.traceability.rejected} rejected</td></tr>
<tr><th>Impact reports</th><td>{analytics.impacts.total}; maximum risk score {analytics.impacts.maximum_risk_score}</td></tr>
<tr><th>AI index</th><td>{html.escape(analytics.assistant.index_status)}; {analytics.assistant.indexed_chunks} chunks</td></tr>
</tbody></table>
</main></body></html>"""
