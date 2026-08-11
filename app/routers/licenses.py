import httpx
from fastapi import APIRouter, HTTPException

from app.schemas import DependencyInput
from app.services.deps_dev import query_deps_dev


router = APIRouter(
    prefix="/dependencies",
    tags=["Licences et métadonnées"],
)


@router.post("/licenses")
async def analyze_dependency_licenses(
    dependency: DependencyInput,
) -> dict[str, object]:
    try:
        metadata = await query_deps_dev(dependency)
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail="Le service deps.dev est temporairement indisponible.",
        ) from error

    licenses = metadata.get("licenses", [])

    return {
        "dependency": dependency.model_dump(),
        "license_count": len(licenses),
        "licenses": licenses,
        "published_at": metadata.get("published_at"),
        "is_deprecated": metadata.get("is_deprecated"),
        "deprecated_reason": metadata.get("deprecated_reason"),
        "links": metadata.get("links", []),
        "registries": metadata.get("registries", []),
        "related_projects": metadata.get(
            "related_projects",
            [],
        ),
        "metadata_status": metadata.get("metadata_status"),
    }