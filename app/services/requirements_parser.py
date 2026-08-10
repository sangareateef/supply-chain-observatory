from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from app.schemas import DependencyInput


def parse_requirements_txt(content: str) -> list[DependencyInput]:
    dependencies: list[DependencyInput] = []

    for line_number, raw_line in enumerate(
        content.splitlines(),
        start=1,
    ):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        line = line.split(" #", maxsplit=1)[0].strip()

        try:
            requirement = Requirement(line)
        except InvalidRequirement as error:
            raise ValueError(
                f"Ligne {line_number} invalide : {line}"
            ) from error

        exact_versions = [
            specifier.version
            for specifier in requirement.specifier
            if specifier.operator == "=="
            and "*" not in specifier.version
        ]

        if len(exact_versions) != 1:
            raise ValueError(
                f"La ligne {line_number} doit fixer une version "
                f"exacte avec == : {line}"
            )

        dependencies.append(
            DependencyInput(
                ecosystem="PyPI",
                name=canonicalize_name(requirement.name),
                version=exact_versions[0],
            )
        )

    if not dependencies:
        raise ValueError(
            "Le fichier ne contient aucune dépendance exploitable."
        )

    return dependencies