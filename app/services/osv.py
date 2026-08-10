from typing import Any

import httpx

from app.schemas import DependencyInput


OSV_QUERY_URL = "https://api.osv.dev/v1/query"
OSV_BATCH_QUERY_URL = "https://api.osv.dev/v1/querybatch"


async def query_osv(
    dependency: DependencyInput,
) -> list[dict[str, Any]]:
    payload = {
        "version": dependency.version,
        "package": {
            "name": dependency.name,
            "ecosystem": dependency.ecosystem,
        },
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            OSV_QUERY_URL,
            json=payload,
        )
        response.raise_for_status()

    data = response.json()
    return data.get("vulns", [])


async def query_osv_batch(
    dependencies: list[DependencyInput],
) -> list[list[dict[str, Any]]]:
    payload = {
        "queries": [
            {
                "version": dependency.version,
                "package": {
                    "name": dependency.name,
                    "ecosystem": dependency.ecosystem,
                },
            }
            for dependency in dependencies
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            OSV_BATCH_QUERY_URL,
            json=payload,
        )
        response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    if len(results) != len(dependencies):
        raise RuntimeError(
            "Le nombre de résultats retournés par OSV est incohérent."
        )

    return [
        result.get("vulns", [])
        for result in results
    ]