import httpx
from fastapi import FastAPI, HTTPException

from app.schemas import DependencyInput
from app.services.osv import query_osv


app = FastAPI(
    title="Observatoire du risque supply chain open source",
    description="API d'analyse des dépendances Python et JavaScript.",
    version="0.2.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Supply Chain Observatory",
        "status": "running",
        "version": "0.2.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/dependencies/analyze")
async def analyze_dependency(
    dependency: DependencyInput,
) -> dict[str, object]:
    try:
        vulnerabilities = await query_osv(dependency)
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail="Le service OSV est temporairement indisponible.",
        ) from error

    vulnerability_summaries = [
        {
            "id": vulnerability.get("id"),
            "summary": vulnerability.get(
                "summary",
                "Résumé non disponible",
            ),
            "aliases": vulnerability.get("aliases", []),
            "modified": vulnerability.get("modified"),
        }
        for vulnerability in vulnerabilities
    ]

    return {
        "dependency": dependency.model_dump(),
        "vulnerability_count": len(vulnerability_summaries),
        "vulnerabilities": vulnerability_summaries,
        "status": "completed",
    }