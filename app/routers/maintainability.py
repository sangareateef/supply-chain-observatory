from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from app.schemas import DependencyInput
from app.services.deps_dev import query_deps_dev
from app.services.maintainability import (
    extract_project_id,
    query_project,
    summarize_project,
)


router = APIRouter(tags=["Maintenabilité"])


def unavailable_response(
    dependency: DependencyInput,
    reason: str,
) -> dict[str, Any]:
    return {
        "dependency": dependency.model_dump(),
        "project": None,
        "activity": {
            "score": None,
            "max_score": 10,
            "level": "unavailable",
            "label": "Indisponible",
            "reason": reason,
        },
        "scorecard": {
            "overall_score": None,
            "date": None,
            "selected_checks": {},
        },
        "status": "unavailable",
    }


@router.post("/dependencies/maintainability")
async def analyze_maintainability(
    dependency: DependencyInput,
) -> dict[str, Any]:
    try:
        metadata = await query_deps_dev(dependency)
        project_id = extract_project_id(metadata)

        if not project_id:
            return unavailable_response(
                dependency,
                (
                    "Aucun dépôt source associé à cette "
                    "version n’a été identifié."
                ),
            )

        project_data = await query_project(project_id)

        if project_data is None:
            return unavailable_response(
                dependency,
                (
                    "Le dépôt source n’est pas connu "
                    "de deps.dev."
                ),
            )

        summary = summarize_project(project_data)

        return {
            "dependency": dependency.model_dump(),
            **summary,
        }

    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "Impossible de récupérer les informations "
                "de maintenabilité."
            ),
        ) from error
        