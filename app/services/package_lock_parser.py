import json
from typing import Any

from app.schemas import DependencyInput


def parse_package_lock(
    content: str,
) -> list[DependencyInput]:
    try:
        data: Any = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Le fichier package-lock.json contient du JSON invalide."
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            "La racine du fichier doit être un objet JSON."
        )

    lockfile_version = data.get("lockfileVersion")

    if lockfile_version not in (2, 3):
        raise ValueError(
            "Seuls les package-lock.json de versions 2 et 3 "
            "sont actuellement acceptés."
        )

    packages = data.get("packages")

    if not isinstance(packages, dict):
        raise ValueError(
            "La section packages est absente ou invalide."
        )

    dependencies: list[DependencyInput] = []
    seen: set[tuple[str, str]] = set()

    for package_path, metadata in packages.items():
        if (
            "node_modules/" not in package_path
            or not isinstance(metadata, dict)
            or metadata.get("link") is True
        ):
            continue

        name = package_path.rsplit(
            "node_modules/",
            maxsplit=1,
        )[-1]
        version = metadata.get("version")

        if not isinstance(version, str) or not version:
            continue

        if version.startswith(
            ("file:", "git+", "http://", "https://")
        ):
            continue

        key = (name, version)

        if key in seen:
            continue

        seen.add(key)
        dependencies.append(
            DependencyInput(
                ecosystem="npm",
                name=name,
                version=version,
            )
        )

    if not dependencies:
        raise ValueError(
            "Le fichier ne contient aucune dépendance npm exploitable."
        )

    return dependencies