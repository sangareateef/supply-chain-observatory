from typing import Any

import httpx

from app.schemas import DependencyInput


OSV_QUERY_URL = "https://api.osv.dev/v1/query"


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
        response = await client.post(OSV_QUERY_URL, json=payload)
        response.raise_for_status()

    data = response.json()
    return data.get("vulns", [])