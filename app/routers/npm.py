import httpx
from fastapi import APIRouter, HTTPException, UploadFile

from app.schemas import DependencyInput
from app.services.osv import query_osv_batch
from app.services.package_lock_parser import parse_package_lock


router = APIRouter(
    prefix="/files/package-lock",
    tags=["JavaScript / npm"],
)

MAX_PACKAGE_LOCK_FILE_SIZE = 1_000_000


async def read_package_lock_upload(
    file: UploadFile,
) -> tuple[str, list[DependencyInput]]:
    filename = file.filename

    if not filename or not filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Un fichier .json est obligatoire.",
        )

    raw_content = await file.read(
        MAX_PACKAGE_LOCK_FILE_SIZE + 1
    )
    await file.close()

    if len(raw_content) > MAX_PACKAGE_LOCK_FILE_SIZE:
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
        dependencies = parse_package_lock(content)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return filename, dependencies


@router.post("/preview")
async def preview_package_lock(
    file: UploadFile,
) -> dict[str, object]:
    filename, dependencies = await read_package_lock_upload(file)

    return {
        "filename": filename,
        "ecosystem": "npm",
        "dependency_count": len(dependencies),
        "dependencies": [
            dependency.model_dump()
            for dependency in dependencies
        ],
        "status": "parsed",
    }


@router.post("/analyze")
async def analyze_package_lock(
    file: UploadFile,
) -> dict[str, object]:
    filename, dependencies = await read_package_lock_upload(file)

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
        "ecosystem": "npm",
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