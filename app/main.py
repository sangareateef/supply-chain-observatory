import httpx
from fastapi import FastAPI, HTTPException, UploadFile

from app.schemas import DependencyInput
from app.services.osv import query_osv, query_osv_batch
from app.services.requirements_parser import parse_requirements_txt
from app.routers.licenses import router as licenses_router
from app.routers.npm import router as npm_router

MAX_REQUIREMENTS_FILE_SIZE = 1_000_000


app = FastAPI(
    title="Observatoire du risque supply chain open source",
    description="API d'analyse des dépendances Python et JavaScript.",
    version="0.6.0",
)
app.include_router(licenses_router)
app.include_router(npm_router)


async def read_requirements_upload(
    file: UploadFile,
) -> tuple[str, list[DependencyInput]]:
    filename = file.filename

    if not filename or not filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Un fichier .txt est obligatoire.",
        )

    raw_content = await file.read(
        MAX_REQUIREMENTS_FILE_SIZE + 1
    )
    await file.close()

    if len(raw_content) > MAX_REQUIREMENTS_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Le fichier dépasse la taille maximale autorisée.",
        )

    try:
        content = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être encodé en UTF-8.",
        ) from error

    try:
        dependencies = parse_requirements_txt(content)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return filename, dependencies


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Supply Chain Observatory",
        "status": "running",
        "version": "0.6.0",
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


@app.post("/files/requirements/preview")
async def preview_requirements_file(
    file: UploadFile,
) -> dict[str, object]:
    filename, dependencies = await read_requirements_upload(file)

    return {
        "filename": filename,
        "dependency_count": len(dependencies),
        "dependencies": [
            dependency.model_dump()
            for dependency in dependencies
        ],
        "status": "parsed",
    }


@app.post("/files/requirements/analyze")
async def analyze_requirements_file(
    file: UploadFile,
) -> dict[str, object]:
    filename, dependencies = await read_requirements_upload(file)

    try:
        vulnerability_groups = await query_osv_batch(dependencies)
    except (httpx.HTTPError, RuntimeError) as error:
        raise HTTPException(
            status_code=502,
            detail="Le service OSV est temporairement indisponible.",
        ) from error

    analyses: list[dict[str, object]] = []
    total_vulnerability_count = 0
    vulnerable_dependency_count = 0

    for dependency, vulnerabilities in zip(
        dependencies,
        vulnerability_groups,
        strict=True,
    ):
        vulnerability_count = len(vulnerabilities)
        total_vulnerability_count += vulnerability_count

        if vulnerability_count > 0:
            vulnerable_dependency_count += 1

        analyses.append(
            {
                "dependency": dependency.model_dump(),
                "vulnerability_count": vulnerability_count,
                "vulnerabilities": vulnerabilities,
            }
        )

    return {
        "filename": filename,
        "dependency_count": len(dependencies),
        "vulnerable_dependency_count": (
            vulnerable_dependency_count
        ),
        "total_vulnerability_count": (
            total_vulnerability_count
        ),
        "analyses": analyses,
        "status": "completed",
    }
  