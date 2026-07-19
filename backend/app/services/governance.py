from __future__ import annotations

from typing import Iterable

from app.models.requirement import Requirement


BASELINE_COMPARE_FIELDS = (
    "title",
    "description",
    "requirement_type",
    "non_functional_category",
    "status",
    "version",
)


def requirement_snapshot(requirement: Requirement) -> dict[str, object]:
    return {
        "id": str(requirement.id),
        "code": requirement.code,
        "title": requirement.title,
        "description": requirement.description,
        "requirement_type": requirement.requirement_type.value,
        "non_functional_category": requirement.non_functional_category,
        "status": requirement.status.value,
        "version": requirement.version,
        "ambiguity_score": requirement.ambiguity_score,
        "ambiguity_flags": list(requirement.ambiguity_flags),
    }


def compare_baseline_snapshots(
    baseline_snapshots: Iterable[dict[str, object]],
    current_snapshots: Iterable[dict[str, object]],
) -> dict[str, object]:
    baseline_by_code = {
        str(snapshot["code"]): snapshot
        for snapshot in baseline_snapshots
    }
    current_by_code = {
        str(snapshot["code"]): snapshot
        for snapshot in current_snapshots
    }

    added: list[dict[str, object]] = []
    modified: list[dict[str, object]] = []
    removed: list[dict[str, object]] = []
    unchanged: list[str] = []

    for code, current in sorted(current_by_code.items()):
        baseline = baseline_by_code.get(code)
        if baseline is None:
            added.append(
                {
                    "code": code,
                    "changed_fields": [],
                    "baseline": None,
                    "current": current,
                }
            )
            continue

        changed_fields = [
            field
            for field in BASELINE_COMPARE_FIELDS
            if baseline.get(field) != current.get(field)
        ]
        if changed_fields:
            modified.append(
                {
                    "code": code,
                    "changed_fields": changed_fields,
                    "baseline": baseline,
                    "current": current,
                }
            )
        else:
            unchanged.append(code)

    for code, baseline in sorted(baseline_by_code.items()):
        if code not in current_by_code:
            removed.append(
                {
                    "code": code,
                    "changed_fields": [],
                    "baseline": baseline,
                    "current": None,
                }
            )

    return {
        "added": added,
        "modified": modified,
        "removed": removed,
        "unchanged": unchanged,
    }
