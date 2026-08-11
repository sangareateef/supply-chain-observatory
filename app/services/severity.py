from typing import Any


SEVERITY_ALIASES = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MODERATE": "moderate",
    "MEDIUM": "moderate",
    "LOW": "low",
}


def _normalize_severity(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    normalized_value = value.strip().upper()
    return SEVERITY_ALIASES.get(normalized_value)


def extract_severity(vulnerability: dict[str, Any]) -> str:
    candidates: list[object] = []

    database_specific = vulnerability.get("database_specific")
    if isinstance(database_specific, dict):
        candidates.append(database_specific.get("severity"))

    severity_entries = vulnerability.get("severity", [])
    if isinstance(severity_entries, list):
        for entry in severity_entries:
            if isinstance(entry, dict):
                candidates.append(entry.get("score"))

    affected_entries = vulnerability.get("affected", [])
    if isinstance(affected_entries, list):
        for affected in affected_entries:
            if not isinstance(affected, dict):
                continue

            for field_name in (
                "database_specific",
                "ecosystem_specific",
            ):
                field_value = affected.get(field_name)

                if isinstance(field_value, dict):
                    candidates.append(field_value.get("severity"))

    for candidate in candidates:
        severity = _normalize_severity(candidate)

        if severity is not None:
            return severity

    return "unknown"


def summarize_severities(
    vulnerabilities: list[dict[str, Any]],
) -> dict[str, int]:
    counts = {
        "critical": 0,
        "high": 0,
        "moderate": 0,
        "low": 0,
        "unknown": 0,
    }

    for vulnerability in vulnerabilities:
        severity = extract_severity(vulnerability)
        counts[severity] += 1

    return counts

SEVERITY_WEIGHTS = {
    "critical": 50,
    "high": 25,
    "moderate": 7,
    "low": 2,
    "unknown": 3,
}

MAX_VULNERABILITY_POINTS = 55


def calculate_vulnerability_points(
    severity_counts: dict[str, int],
) -> int:
    raw_score = sum(
        severity_counts.get(level, 0) * weight
        for level, weight in SEVERITY_WEIGHTS.items()
    )

    return min(MAX_VULNERABILITY_POINTS, raw_score)