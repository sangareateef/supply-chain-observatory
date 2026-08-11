import asyncio
from typing import Any
from urllib.parse import quote

import httpx

from app.schemas import DependencyInput


DEPS_DEV_BASE_URL = "https://api.deps.dev/v3"

ECOSYSTEM_TO_SYSTEM = {
    "PyPI": "PYPI",
    "npm": "NPM",
}


def build_version_url(
    dependency: DependencyInput,
) -> str:
    system = ECOSYSTEM_TO_SYSTEM[dependency.ecosystem]
    package_name = quote(dependency.name, safe="")
    version = quote(dependency.version, safe="")

    return (
        f"{DEPS_DEV_BASE_URL}/systems/{system}"
        f"/packages/{package_name}/versions/{version}"
    )


async def query_deps_dev(
    dependency: DependencyInput,
) -> dict[str, Any]:
    url = build_version_url(dependency)

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url)

    if response.status_code == 404:
        return {
            "licenses": [],
            "published_at": None,
            "is_deprecated": False,
            "deprecated_reason": None,
            "links": [],
            "registries": [],
            "related_projects": [],
            "metadata_status": "not_found",
        }

    response.raise_for_status()
    data = response.json()

    return {
        "licenses": data.get("licenses") or [],
        "published_at": data.get("publishedAt"),
        "is_deprecated": data.get("isDeprecated", False),
        "deprecated_reason": data.get("deprecatedReason"),
        "links": data.get("links") or [],
        "registries": data.get("registries") or [],
        "related_projects": data.get("relatedProjects") or [],
        "metadata_status": "found",
    }


async def query_deps_dev_batch(
    dependencies: list[DependencyInput],
) -> list[dict[str, Any]]:
    results = await asyncio.gather(
        *(
            query_deps_dev(dependency)
            for dependency in dependencies
        )
    )

    return list(results)