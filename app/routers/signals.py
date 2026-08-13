from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from app.schemas import DependencyInput
from app.services.registry_metadata import query_registry_metadata
from app.services.suspicious_signals import detect_suspicious_signals


router = APIRouter(
    prefix="/dependencies",
    tags=["Signaux suspects"],
)


@router.post("/signals")
async def analyze_suspicious_signals(
    dependency: DependencyInput,
) -> dict[str, Any]:
    try:
        registry_metadata = await query_registry_metadata(dependency)
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="Impossible de récupérer les métadonnées du registre.",
        ) from error

    analysis = detect_suspicious_signals(
        dependency=dependency,
        registry_metadata=registry_metadata,
    )

    return {
        **analysis,
        "registry_metadata": registry_metadata,
        "status": "completed",
    }