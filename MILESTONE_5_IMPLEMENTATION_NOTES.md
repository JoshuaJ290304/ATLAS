# ATLAS Milestone 5 Implementation Notes

## Scope

Milestone 5 implements change-impact analysis and closes the two visual defects recorded after Milestone 4 testing.

## Data model

### `requirement_versions`

Stores an immutable snapshot whenever a requirement is created, extracted, or edited. The unique key is `(requirement_id, version)`.

### `impact_analyses`

Stores a complete report including requirement identity, compared versions, change type, risk score, severity, differences, direct/transitive artifact snapshots, risk factors, and summary.

## Change comparison

ATLAS compares title, description, type, non-functional category, status, ambiguity score, and ambiguity flags. It also records text similarity, change ratio, added/removed terms, and a unified text diff.

## Impact graph

Only accepted trace links are used:

1. Direct artifacts are accepted-linked to the changed requirement.
2. A bridge requirement is accepted-linked to a direct artifact.
3. Other artifacts accepted-linked to that bridge requirement are transitive impacts.
4. Each transitive result stores its trace path.

Suggested and rejected links remain outside the impact graph.

## Risk score

The deterministic score is capped at 100 and combines:

- Change magnitude: 30 points
- Direct artifact scope: 30 points
- Transitive scope: 15 points
- Requirement lifecycle status: 10 points
- Ambiguity/high-risk quality category: 10 points
- Traceability uncertainty: 5 points

Severity thresholds:

- Low: 0–24
- Medium: 25–49
- High: 50–74
- Critical: 75–100

## Compatibility note

Requirements created before migration `0005` have no historical snapshots. ATLAS lazily saves the currently available state as the first snapshot. Future edits are fully versioned.

## UI corrections

Project-card actions now use a responsive 2×2 grid. Traceability metrics include rejected links. An Impact button is available on every project card.
