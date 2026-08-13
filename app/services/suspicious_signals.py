from typing import Any

from app.schemas import DependencyInput


SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
}

SEVERITY_LABELS = {
    "none": "Aucun",
    "low": "Faible",
    "medium": "Moyen",
    "high": "Élevé",
}


def _add_signal(
    signals: list[dict[str, Any]],
    *,
    code: str,
    severity: str,
    title: str,
    description: str,
    evidence: dict[str, Any],
    recommendation: str,
) -> None:
    signals.append(
        {
            "code": code,
            "severity": severity,
            "severity_label": SEVERITY_LABELS[severity],
            "title": title,
            "description": description,
            "evidence": evidence,
            "recommendation": recommendation,
        }
    )


def _highest_severity(
    signals: list[dict[str, Any]],
) -> str:
    if not signals:
        return "none"

    return max(
        (
            str(signal["severity"])
            for signal in signals
        ),
        key=lambda severity: SEVERITY_ORDER[severity],
    )


def _is_missing_text(value: Any) -> bool:
    if value is None:
        return True

    normalized_value = str(value).strip().casefold()

    return normalized_value in {
        "",
        "unknown",
        "none",
        "n/a",
    }


def detect_suspicious_signals(
    *,
    dependency: DependencyInput,
    registry_metadata: dict[str, Any],
) -> dict[str, Any]:
    signals: list[dict[str, Any]] = []

    registry_status = str(
        registry_metadata.get("registry_status")
        or "unknown"
    )

    if registry_status == "not_found":
        _add_signal(
            signals,
            code="version_not_found",
            severity="high",
            title="Version absente du registre",
            description=(
                "La version demandée n’a pas été trouvée "
                "dans le registre officiel."
            ),
            evidence={
                "registry_status": registry_status,
            },
            recommendation=(
                "Vérifier le nom du paquet et sa version "
                "avant toute installation."
            ),
        )

    elif registry_status != "found":
        _add_signal(
            signals,
            code="registry_metadata_unavailable",
            severity="low",
            title="Métadonnées du registre indisponibles",
            description=(
                "Les informations du registre officiel "
                "n’ont pas pu être confirmées."
            ),
            evidence={
                "registry_status": registry_status,
            },
            recommendation=(
                "Relancer l’analyse et vérifier manuellement "
                "le paquet dans son registre officiel."
            ),
        )

    else:
        if registry_metadata.get("is_yanked") is True:
            _add_signal(
                signals,
                code="yanked_version",
                severity="high",
                title="Version retirée du registre",
                description=(
                    "Cette version a été retirée du registre. "
                    "Un retrait peut avoir plusieurs causes."
                ),
                evidence={
                    "yanked_reason": registry_metadata.get(
                        "yanked_reason"
                    ),
                },
                recommendation=(
                    "Examiner la raison du retrait et utiliser "
                    "une version maintenue si possible."
                ),
            )

        deprecation_message = registry_metadata.get(
            "deprecation_message"
        )

        if not _is_missing_text(deprecation_message):
            _add_signal(
                signals,
                code="deprecated_version",
                severity="medium",
                title="Version déclarée obsolète",
                description=(
                    "Le registre indique que cette version "
                    "est obsolète."
                ),
                evidence={
                    "deprecation_message": deprecation_message,
                },
                recommendation=(
                    "Consulter le message du mainteneur et "
                    "préparer une mise à jour."
                ),
            )

        install_scripts = registry_metadata.get(
            "install_scripts"
        )

        if isinstance(install_scripts, list):
            script_names = [
                str(script)
                for script in install_scripts
                if str(script).strip()
            ]
        else:
            script_names = []

        if script_names:
            _add_signal(
                signals,
                code="install_lifecycle_scripts",
                severity="medium",
                title="Scripts exécutables pendant l’installation",
                description=(
                    "Le paquet déclare des scripts pouvant être "
                    "lancés pendant son installation."
                ),
                evidence={
                    "scripts": script_names,
                },
                recommendation=(
                    "Examiner le contenu de ces scripts avant "
                    "d’installer le paquet."
                ),
            )

        repository_url = registry_metadata.get(
            "repository_url"
        )

        if _is_missing_text(repository_url):
            _add_signal(
                signals,
                code="missing_source_repository",
                severity="low",
                title="Dépôt source non identifié",
                description=(
                    "Aucun dépôt de code source n’a été identifié "
                    "dans les métadonnées officielles."
                ),
                evidence={
                    "repository_url": repository_url,
                },
                recommendation=(
                    "Rechercher le dépôt officiel et vérifier "
                    "son lien avec le paquet."
                ),
            )

        declared_license = registry_metadata.get(
            "declared_license"
        )

        if _is_missing_text(declared_license):
            _add_signal(
                signals,
                code="missing_declared_license",
                severity="low",
                title="Licence non identifiée",
                description=(
                    "Aucune licence claire n’a été trouvée "
                    "dans les métadonnées du registre."
                ),
                evidence={
                    "declared_license": declared_license,
                },
                recommendation=(
                    "Vérifier manuellement la licence avant "
                    "d’intégrer le paquet."
                ),
            )

    highest_severity = _highest_severity(signals)

    return {
        "dependency": dependency.model_dump(),
        "signal_count": len(signals),
        "highest_severity": highest_severity,
        "highest_severity_label": (
            SEVERITY_LABELS[highest_severity]
        ),
        "review_recommended": bool(signals),
        "signals": signals,
        "interpretation": (
            "Ces signaux sont des indicateurs destinés à une "
            "vérification humaine. Ils ne constituent pas une "
            "preuve de malveillance."
        ),
    }