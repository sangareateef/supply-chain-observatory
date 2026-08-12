from typing import Any
from urllib.parse import quote, urlparse

import httpx


DEPS_DEV_BASE_URL = "https://api.deps.dev/v3"
PROJECT_HOSTS = {
    "github.com",
    "gitlab.com",
    "bitbucket.org",
}


def project_id_from_url(url: str) -> str | None:
    parsed_url = urlparse(url)
    host = parsed_url.netloc.lower()

    if host not in PROJECT_HOSTS:
        return None

    path_parts = [
        part
        for part in parsed_url.path.strip("/").split("/")
        if part
    ]

    if len(path_parts) < 2:
        return None

    owner = path_parts[0]
    repository = path_parts[1].removesuffix(".git")

    return f"{host}/{owner}/{repository}"


def extract_project_id(
    metadata: dict[str, Any],
) -> str | None:
    related_projects = metadata.get("related_projects", [])

    ordered_projects = sorted(
        related_projects,
        key=lambda project: (
            0
            if project.get("relationType") == "SOURCE_REPO"
            else 1
        ),
    )

    for project in ordered_projects:
        project_key = (
            project.get("projectKey")
            or project.get("project_key")
            or {}
        )
        project_id = project_key.get("id")

        if isinstance(project_id, str) and project_id:
            return project_id

    for link in metadata.get("links", []):
        label = str(link.get("label", "")).upper()

        if label not in {
            "SOURCE_REPO",
            "REPOSITORY",
            "ORIGIN",
            "HOMEPAGE",
        }:
            continue

        project_id = project_id_from_url(
            str(link.get("url", ""))
        )

        if project_id:
            return project_id

    return None


async def query_project(
    project_id: str,
) -> dict[str, Any] | None:
    encoded_project_id = quote(project_id, safe="")
    url = (
        f"{DEPS_DEV_BASE_URL}/projects/"
        f"{encoded_project_id}"
    )

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
    ) as client:
        response = await client.get(url)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    project_data = response.json()

    if not isinstance(project_data, dict):
        raise ValueError(
            "La réponse de deps.dev est invalide."
        )

    return project_data

SELECTED_CHECKS = (
    "Maintained",
    "Code-Review",
    "CI-Tests",
    "Dependency-Update-Tool",
)


def get_activity_level(
    score: float | None,
) -> tuple[str, str]:
    if score is None:
        return "unavailable", "Indisponible"

    if score >= 8:
        return "very_active", "Très active"

    if score >= 5:
        return "active", "Active"

    if score >= 2:
        return "limited", "Limitée"

    return "very_low", "Très faible"


def summarize_project(
    project_data: dict[str, Any],
) -> dict[str, Any]:
    project_key = project_data.get("projectKey", {})
    project_id = project_key.get("id")

    scorecard = project_data.get("scorecard") or {}
    scorecard_checks = scorecard.get("checks", [])

    checks_by_name = {
        check.get("name"): check
        for check in scorecard_checks
        if isinstance(check, dict) and check.get("name")
    }

    maintained_check = checks_by_name.get("Maintained")
    activity_score: float | None = None
    activity_reason: str | None = None

    if maintained_check:
        raw_score = maintained_check.get("score")

        if (
            isinstance(raw_score, (int, float))
            and raw_score >= 0
        ):
            activity_score = float(raw_score)

        activity_reason = maintained_check.get("reason")

    activity_level, activity_label = get_activity_level(
        activity_score
    )

    selected_checks: dict[str, dict[str, Any]] = {}

    for check_name in SELECTED_CHECKS:
        check = checks_by_name.get(check_name)

        if not check:
            continue

        selected_checks[check_name] = {
            "score": check.get("score"),
            "reason": check.get("reason"),
        }

    return {
        "project": {
            "id": project_id,
            "url": (
                f"https://{project_id}"
                if project_id
                else None
            ),
            "description": project_data.get("description"),
            "homepage": project_data.get("homepage"),
            "license": project_data.get("license"),
            "stars_count": project_data.get("starsCount"),
            "forks_count": project_data.get("forksCount"),
            "open_issues_count": project_data.get(
                "openIssuesCount"
            ),
        },
        "activity": {
            "score": activity_score,
            "max_score": 10,
            "level": activity_level,
            "label": activity_label,
            "reason": activity_reason,
        },
        "scorecard": {
            "overall_score": scorecard.get(
                "overallScore"
            ),
            "date": scorecard.get("date"),
            "selected_checks": selected_checks,
        },
        "status": "completed",
    }