from datetime import UTC, datetime
from typing import Any


def parse_published_at(
    published_at: str | None,
) -> datetime | None:
    if not published_at:
        return None

    try:
        parsed_date = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )
    except ValueError:
        return None

    if parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=UTC)

    return parsed_date


def has_source_repository(
    links: list[dict[str, Any]],
    related_projects: list[dict[str, Any]],
) -> bool:
    for link in links:
        label = str(link.get("label", "")).upper()

        if label == "SOURCE_REPO":
            return True

    for project in related_projects:
        relation_type = str(
            project.get("relationType", "")
        ).upper()

        if relation_type == "SOURCE_REPO":
            return True

    return False


def calculate_risk_score(
    *,
    vulnerability_count: int,
    licenses: list[str],
    is_deprecated: bool,
    published_at: str | None,
    metadata_status: str | None,
    links: list[dict[str, Any]],
    related_projects: list[dict[str, Any]],
) -> dict[str, Any]:
    breakdown = {
        "vulnerabilities": 0,
        "license": 0,
        "deprecation": 0,
        "age": 0,
        "metadata": 0,
    }
    reasons: list[str] = []

    if vulnerability_count >= 10:
        breakdown["vulnerabilities"] = 55
    elif vulnerability_count >= 5:
        breakdown["vulnerabilities"] = 45
    elif vulnerability_count >= 2:
        breakdown["vulnerabilities"] = 35
    elif vulnerability_count == 1:
        breakdown["vulnerabilities"] = 20

    if vulnerability_count > 0:
        reasons.append(
            f"{vulnerability_count} vulnérabilité(s) connue(s)."
        )

    normalized_licenses = " ".join(licenses).upper()

    if not licenses:
        breakdown["license"] = 15
        reasons.append("Licence non renseignée.")
    elif "NON-STANDARD" in normalized_licenses:
        breakdown["license"] = 15
        reasons.append("Licence non standard.")
    elif (
        "AGPL" in normalized_licenses
        or "SSPL" in normalized_licenses
        or (
            "GPL" in normalized_licenses
            and "LGPL" not in normalized_licenses
        )
    ):
        breakdown["license"] = 10
        reasons.append(
            "Licence comportant des contraintes fortes."
        )
    elif any(
        marker in normalized_licenses
        for marker in ("LGPL", "MPL", "EPL", "CDDL")
    ):
        breakdown["license"] = 5
        reasons.append(
            "Licence comportant certaines contraintes."
        )

    if is_deprecated:
        breakdown["deprecation"] = 15
        reasons.append(
            "Cette version est déclarée obsolète."
        )

    published_date = parse_published_at(published_at)
    age_years: float | None = None

    if published_date is not None:
        age_days = (
            datetime.now(UTC) - published_date
        ).days
        age_years = max(0.0, age_days / 365.25)

        if age_years >= 5:
            breakdown["age"] = 10
            reasons.append(
                "Version publiée depuis au moins cinq ans."
            )
        elif age_years >= 3:
            breakdown["age"] = 5
            reasons.append(
                "Version publiée depuis au moins trois ans."
            )

    if metadata_status != "found":
        breakdown["metadata"] = 5
        reasons.append(
            "Métadonnées du paquet introuvables."
        )
    elif not has_source_repository(
        links,
        related_projects,
    ):
        breakdown["metadata"] = 5
        reasons.append(
            "Dépôt du code source non identifié."
        )

    score = min(100, sum(breakdown.values()))

    if score >= 80:
        level = "critical"
        level_label = "Critique"
    elif score >= 50:
        level = "high"
        level_label = "Élevé"
    elif score >= 25:
        level = "moderate"
        level_label = "Modéré"
    else:
        level = "low"
        level_label = "Faible"

    if not reasons:
        reasons.append(
            "Aucun signal de risque majeur détecté."
        )

    return {
        "score": score,
        "max_score": 100,
        "level": level,
        "level_label": level_label,
        "score_version": "1.0",
        "age_years": (
            round(age_years, 1)
            if age_years is not None
            else None
        ),
        "breakdown": breakdown,
        "reasons": reasons,
    }