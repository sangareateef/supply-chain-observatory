from typing import Any
from urllib.parse import quote

import httpx

from app.schemas import DependencyInput


NPM_REGISTRY_BASE_URL = "https://registry.npmjs.org"
PYPI_JSON_BASE_URL = "https://pypi.org/pypi"
REQUEST_TIMEOUT_SECONDS = 15.0

NPM_INSTALL_SCRIPTS = (
    "preinstall",
    "install",
    "postinstall",
)


def _text_or_none(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None

    return None


def _npm_repository_url(value: Any) -> str | None:
    if isinstance(value, str):
        return _text_or_none(value)

    if isinstance(value, dict):
        return _text_or_none(value.get("url"))

    return None


def _pypi_repository_url(info: dict[str, Any]) -> str | None:
    project_urls = info.get("project_urls")

    if isinstance(project_urls, dict):
        preferred_words = (
            "source",
            "repository",
            "code",
            "github",
        )

        for label, url in project_urls.items():
            normalized_label = str(label).casefold()

            if any(
                word in normalized_label
                for word in preferred_words
            ):
                repository_url = _text_or_none(url)

                if repository_url:
                    return repository_url

    return None


def _pypi_license(info: dict[str, Any]) -> str | None:
    declared_license = _text_or_none(info.get("license"))

    if declared_license:
        return declared_license

    classifiers = info.get("classifiers", [])

    if not isinstance(classifiers, list):
        return None

    license_classifiers = [
        classifier
        for classifier in classifiers
        if isinstance(classifier, str)
        and classifier.startswith("License ::")
    ]

    if not license_classifiers:
        return None

    return "; ".join(license_classifiers)


def _empty_result() -> dict[str, Any]:
    return {
        "registry_status": "not_found",
        "install_scripts": [],
        "is_yanked": False,
        "yanked_reason": None,
        "repository_url": None,
        "declared_license": None,
        "deprecation_message": None,
    }


async def _query_npm(
    dependency: DependencyInput,
) -> dict[str, Any]:
    package_name = quote(dependency.name, safe="")
    package_version = quote(dependency.version, safe="")

    url = (
        f"{NPM_REGISTRY_BASE_URL}/"
        f"{package_name}/{package_version}"
    )

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
    ) as client:
        response = await client.get(
            url,
            headers={"Accept": "application/json"},
        )

    if response.status_code == 404:
        return _empty_result()

    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            "La réponse du registre npm est invalide."
        )

    scripts = data.get("scripts")

    if not isinstance(scripts, dict):
        scripts = {}

    install_scripts = [
        script_name
        for script_name in NPM_INSTALL_SCRIPTS
        if _text_or_none(scripts.get(script_name))
    ]

    license_value = data.get("license")

    if isinstance(license_value, dict):
        declared_license = _text_or_none(
            license_value.get("type")
        )
    else:
        declared_license = _text_or_none(license_value)

    return {
        "registry_status": "found",
        "install_scripts": install_scripts,
        "is_yanked": False,
        "yanked_reason": None,
        "repository_url": _npm_repository_url(
            data.get("repository")
        ),
        "declared_license": declared_license,
        "deprecation_message": _text_or_none(
            data.get("deprecated")
        ),
    }


async def _query_pypi(
    dependency: DependencyInput,
) -> dict[str, Any]:
    package_name = quote(dependency.name, safe="")
    package_version = quote(dependency.version, safe="")

    url = (
        f"{PYPI_JSON_BASE_URL}/"
        f"{package_name}/{package_version}/json"
    )

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
    ) as client:
        response = await client.get(
            url,
            headers={"Accept": "application/json"},
        )

    if response.status_code == 404:
        return _empty_result()

    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            "La réponse de PyPI est invalide."
        )

    info = data.get("info")
    files = data.get("urls")

    if not isinstance(info, dict):
        info = {}

    if not isinstance(files, list):
        files = []

    is_yanked = bool(info.get("yanked"))

    if not is_yanked and files:
        is_yanked = all(
            isinstance(file_data, dict)
            and bool(file_data.get("yanked"))
            for file_data in files
        )

    yanked_reason = _text_or_none(
        info.get("yanked_reason")
    )

    if is_yanked and not yanked_reason:
        for file_data in files:
            if not isinstance(file_data, dict):
                continue

            yanked_reason = _text_or_none(
                file_data.get("yanked_reason")
            )

            if yanked_reason:
                break

    return {
        "registry_status": "found",
        "install_scripts": [],
        "is_yanked": is_yanked,
        "yanked_reason": yanked_reason,
        "repository_url": _pypi_repository_url(info),
        "declared_license": _pypi_license(info),
        "deprecation_message": None,
    }


async def query_registry_metadata(
    dependency: DependencyInput,
) -> dict[str, Any]:
    ecosystem = dependency.ecosystem.casefold()

    if ecosystem == "npm":
        return await _query_npm(dependency)

    if ecosystem == "pypi":
        return await _query_pypi(dependency)

    raise ValueError(
        "Seuls les écosystèmes PyPI et npm sont acceptés."
    )