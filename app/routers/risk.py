import asyncio

import httpx
from fastapi import APIRouter, HTTPException

from app.schemas import DependencyInput
from app.services.deps_dev import query_deps_dev
from app.services.osv import query_osv
from app.services.risk_score import calculate_risk_score

router = APIRouter(
    prefix="/dependencies",
    tags=["Score de risque"],
)


@router.post("/risk")
async def analyze_dependency_risk(
    dependency: DependencyInput,
) -> dict[str, object]:
    try:
        vulnerabilities, metadata = await asyncio.gather(
            query_osv(dependency),
            query_deps_dev(dependency),
        )
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "Un service externe est temporairement "
                "indisponible."
            ),
        ) from error

    licenses = metadata.get("licenses", [])

    risk = calculate_risk_score(
        vulnerability_count=len(vulnerabilities),
        licenses=licenses,
        is_deprecated=bool(
            metadata.get("is_deprecated", False)
        ),
        published_at=metadata.get("published_at"),
        metadata_status=metadata.get("metadata_status"),
        links=metadata.get("links", []),
        related_projects=metadata.get(
            "related_projects",
            [],
        ),
    )

    return {
        "dependency": dependency.model_dump(),
        "vulnerability_count": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
        "licenses": licenses,
        "metadata": metadata,
        "risk": risk,
        "status": "completed",
    }