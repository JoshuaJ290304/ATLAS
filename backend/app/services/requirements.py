from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.requirement import RequirementType

BULLET_PREFIX = re.compile(
    r"^\s*(?:[-*•●▪◦]|\(?\d+(?:\.\d+)*[.)]|(?:FR|NFR|REQ)[-_ ]?\d+[:.)-]?)\s*",
    re.IGNORECASE,
)
WHITESPACE = re.compile(r"\s+")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
STRONG_REQUIREMENT = re.compile(
    r"\b(?:shall|must|required to|is required to|will provide|will allow)\b",
    re.IGNORECASE,
)
WEAK_REQUIREMENT = re.compile(
    r"\b(?:should|may|might|could|can)\b",
    re.IGNORECASE,
)
ACTOR_ACTION = re.compile(
    r"\b(?:system|application|platform|service|user|administrator|admin|operator|customer)\b"
    r".{0,50}\b(?:shall|must|should|can|will)\b",
    re.IGNORECASE,
)

NFR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "performance": (
        "performance",
        "response time",
        "latency",
        "throughput",
        "transactions per second",
        "load time",
        "concurrent users",
    ),
    "security": (
        "security",
        "secure",
        "multi-factor authentication",
        "authorization policy",
        "encrypt",
        "access control",
        "vulnerability",
    ),
    "privacy": ("privacy", "personal data", "confidential", "consent", "data protection"),
    "availability": ("availability", "uptime", "downtime", "24/7", "failover"),
    "reliability": ("reliable", "reliability", "fault tolerance", "recover", "backup"),
    "scalability": ("scalable", "scalability", "scale up", "scale out", "growth"),
    "usability": (
        "usability",
        "user-friendly",
        "easy to use",
        "intuitive",
        "learnability",
    ),
    "accessibility": ("accessibility", "wcag", "screen reader", "keyboard navigation"),
    "maintainability": (
        "maintainability",
        "maintainable",
        "modular",
        "code quality",
        "technical debt",
    ),
    "compatibility": (
        "compatibility",
        "compatible",
        "browser",
        "operating system",
        "interoperability",
    ),
    "compliance": ("compliance", "comply", "regulation", "standard", "audit"),
}

AMBIGUITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Uses subjective or unverifiable wording",
        re.compile(
            r"\b(?:user[- ]friendly|intuitive|easy|simple|fast|quickly|efficient|robust|"
            r"seamless|appropriate|reasonable|minimal|optimal|high quality)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Uses an imprecise quantity",
        re.compile(
            r"\b(?:some|several|many|few|various|adequate|sufficient|enough|frequent|"
            r"occasionally)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Uses a weak modal instead of a binding obligation",
        re.compile(r"\b(?:should|may|might|could)\b", re.IGNORECASE),
    ),
    (
        "Contains an open-ended qualifier",
        re.compile(
            r"\b(?:etc\.?|and/or|as needed|where appropriate|where applicable|if possible|"
            r"when necessary|normally)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Contains an unclear reference",
        re.compile(r"\b(?:this|that|these|those|it|they)\b", re.IGNORECASE),
    ),
)


@dataclass(frozen=True)
class RequirementCandidate:
    title: str
    description: str
    requirement_type: RequirementType
    non_functional_category: str | None
    source_excerpt: str
    source_position: int
    confidence_score: float
    ambiguity_score: int
    ambiguity_flags: list[str]


def normalize_text(value: str) -> str:
    return WHITESPACE.sub(" ", value).strip()


def normalize_for_comparison(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def classify_requirement(text: str) -> tuple[RequirementType, str | None]:
    lowered = text.lower()
    scores = {
        category: sum(1 for keyword in keywords if keyword in lowered)
        for category, keywords in NFR_KEYWORDS.items()
    }
    category, score = max(scores.items(), key=lambda item: item[1])
    if score > 0:
        return RequirementType.NON_FUNCTIONAL, category
    return RequirementType.FUNCTIONAL, None


def analyze_ambiguity(
    text: str,
    requirement_type: RequirementType | None = None,
) -> tuple[int, list[str]]:
    flags = [message for message, pattern in AMBIGUITY_PATTERNS if pattern.search(text)]
    resolved_type = requirement_type or classify_requirement(text)[0]

    if resolved_type == RequirementType.NON_FUNCTIONAL and not re.search(
        r"\b\d+(?:\.\d+)?\s*(?:%|ms|s|sec(?:onds?)?|minutes?|hours?|mb|gb|users?|"
        r"requests?|transactions?)\b",
        text,
        re.IGNORECASE,
    ):
        flags.append("Non-functional requirement lacks a measurable target")

    if len(normalize_text(text).split()) < 6:
        flags.append("Requirement is too short to be independently testable")

    if not re.search(
        r"\b(?:system|application|platform|service|user|admin|administrator)\b",
        text,
        re.I,
    ):
        flags.append("Actor or responsible component is not explicit")

    unique_flags = list(dict.fromkeys(flags))
    return min(100, len(unique_flags) * 20), unique_flags


def make_title(description: str) -> str:
    title = normalize_text(description)
    title = re.sub(
        r"^(?:the\s+)?(?:system|application|platform|service|user|administrator|admin)\s+"
        r"(?:shall|must|should|will|can|is required to)\s+",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = title.rstrip(". ;:")
    if not title:
        title = "Untitled requirement"
    if len(title) > 117:
        title = f"{title[:117].rstrip()}..."
    return title[0].upper() + title[1:]


def _line_candidates(text: str) -> list[tuple[int, str, bool]]:
    candidates: list[tuple[int, str, bool]] = []
    for position, raw_line in enumerate(text.splitlines(), start=1):
        line = normalize_text(raw_line)
        if not line:
            continue
        had_bullet = bool(BULLET_PREFIX.match(line))
        cleaned = BULLET_PREFIX.sub("", line).strip()
        if not cleaned:
            continue

        fragments = SENTENCE_SPLIT.split(cleaned) if len(cleaned) > 350 else [cleaned]
        for fragment in fragments:
            fragment = normalize_text(fragment)
            if fragment:
                candidates.append((position, fragment, had_bullet))
    return candidates


def _is_heading(text: str) -> bool:
    words = text.split()
    if len(words) > 10 or STRONG_REQUIREMENT.search(text) or WEAK_REQUIREMENT.search(text):
        return False
    if text.endswith(('.', ';')):
        return False
    return text.isupper() or text.istitle()


def _is_requirement_candidate(text: str, had_bullet: bool) -> bool:
    word_count = len(text.split())
    if word_count < 5 or len(text) < 25 or len(text) > 1500 or _is_heading(text):
        return False
    if STRONG_REQUIREMENT.search(text) or ACTOR_ACTION.search(text):
        return True
    if had_bullet and (WEAK_REQUIREMENT.search(text) or word_count >= 8):
        return True
    if re.match(r"^(?:FR|NFR|REQ)[-_ ]?\d+", text, re.IGNORECASE):
        return True
    return False


def _confidence(text: str, had_bullet: bool) -> float:
    value = 0.48
    if had_bullet:
        value += 0.12
    if STRONG_REQUIREMENT.search(text):
        value += 0.25
    elif WEAK_REQUIREMENT.search(text):
        value += 0.08
    if ACTOR_ACTION.search(text):
        value += 0.1
    if len(text.split()) >= 10:
        value += 0.05
    return round(min(value, 0.99), 2)


def extract_requirement_candidates(text: str) -> list[RequirementCandidate]:
    results: list[RequirementCandidate] = []
    seen: set[str] = set()

    for position, fragment, had_bullet in _line_candidates(text):
        if not _is_requirement_candidate(fragment, had_bullet):
            continue
        description = normalize_text(fragment)
        normalized = normalize_for_comparison(description)
        if normalized in seen:
            continue
        seen.add(normalized)

        requirement_type, category = classify_requirement(description)
        ambiguity_score, ambiguity_flags = analyze_ambiguity(description, requirement_type)
        results.append(
            RequirementCandidate(
                title=make_title(description),
                description=description,
                requirement_type=requirement_type,
                non_functional_category=category,
                source_excerpt=description,
                source_position=position,
                confidence_score=_confidence(description, had_bullet),
                ambiguity_score=ambiguity_score,
                ambiguity_flags=ambiguity_flags,
            )
        )

    return results
