"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const getElement = (id) => document.getElementById(id);

    const elements = {
        form: getElement("analysis-form"),
        ecosystem: getElement("ecosystem"),
        packageName: getElement("package-name"),
        packageVersion: getElement("package-version"),
        formError: getElement("form-error"),
        analyzeButton: getElement("analyze-button"),

        loadingState: getElement("loading-state"),
        emptyState: getElement("empty-state"),
        resultsSection: getElement("results-section"),
        newAnalysisButton: getElement("new-analysis-button"),

        resultPackageName: getElement("result-package-name"),
        resultPackageMeta: getElement("result-package-meta"),

        riskScore: getElement("risk-score"),
        riskLevel: getElement("risk-level"),
        vulnerabilityCount: getElement("vulnerability-count"),
        licenseValue: getElement("license-value"),
        licenseStatus: getElement("license-status"),
        activityScore: getElement("activity-score"),
        activityLevel: getElement("activity-level"),
        signalCount: getElement("signal-count"),
        signalLevel: getElement("signal-level"),

        riskVulnerabilityPoints: getElement("risk-vulnerability-points"),
        riskLicensePoints: getElement("risk-license-points"),
        riskDeprecationPoints: getElement("risk-deprecation-points"),
        riskAgePoints: getElement("risk-age-points"),
        riskMetadataPoints: getElement("risk-metadata-points"),
        riskReasons: getElement("risk-reasons"),

        severityCritical: getElement("severity-critical"),
        severityHigh: getElement("severity-high"),
        severityModerate: getElement("severity-moderate"),
        severityLow: getElement("severity-low"),
        severityUnknown: getElement("severity-unknown"),

        vulnerabilitiesList: getElement("vulnerabilities-list"),

        projectName: getElement("project-name"),
        projectStars: getElement("project-stars"),
        projectIssues: getElement("project-issues"),
        scorecardScore: getElement("scorecard-score"),

        signalsList: getElement("signals-list"),
    };

    if (!elements.form) {
        console.error("Le formulaire d’analyse est introuvable.");
        return;
    }

    const endpoints = {
        risk: "/dependencies/risk",
        licenses: "/dependencies/licenses",
        maintainability: "/dependencies/maintainability",
        signals: "/dependencies/signals",
    };

    const defaultButtonText =
        elements.analyzeButton?.textContent.trim() || "Analyser";

    function setText(element, value, fallback = "—") {
        if (!element) return;

        const isEmpty =
            value === null ||
            value === undefined ||
            value === "";

        element.textContent = isEmpty ? fallback : String(value);
    }

    function setHidden(element, hidden) {
        if (element) {
            element.hidden = hidden;
        }
    }

    function setError(message = "") {
        if (!elements.formError) return;

        elements.formError.textContent = message;
        elements.formError.hidden = message.length === 0;
    }

    function normalizeLevel(level) {
        return String(level || "unknown")
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[^a-z0-9]+/g, "-");
    }

    function applyLevel(element, level) {
        if (!element) return;

        const normalizedLevel = normalizeLevel(level);
        element.dataset.level = normalizedLevel;

        const card = element.closest(
            ".metric-card, .summary-card, .score-card"
        );

        if (card) {
            card.dataset.level = normalizedLevel;
        }
    }

    function formatNumber(value) {
        if (value === null || value === undefined || value === "") {
            return "—";
        }

        const number = Number(value);

        if (!Number.isFinite(number)) {
            return String(value);
        }

        return new Intl.NumberFormat("fr-FR").format(number);
    }

    function createElement(tagName, className, text) {
        const element = document.createElement(tagName);

        if (className) {
            element.className = className;
        }

        if (text !== undefined) {
            element.textContent = text;
        }

        return element;
    }

    function getErrorMessage(data, status) {
        if (typeof data?.detail === "string") {
            return data.detail;
        }

        if (Array.isArray(data?.detail)) {
            return data.detail
                .map((item) => item.msg || "Donnée invalide")
                .join(", ");
        }

        return `Erreur HTTP ${status}`;
    }

    async function postAnalysis(endpoint, payload) {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        let data = null;

        try {
            data = await response.json();
        } catch {
            data = null;
        }

        if (!response.ok) {
            throw new Error(getErrorMessage(data, response.status));
        }

        return data;
    }

    function showLoading() {
        setHidden(elements.emptyState, true);
        setHidden(elements.resultsSection, true);
        setHidden(elements.loadingState, false);

        if (elements.analyzeButton) {
            elements.analyzeButton.disabled = true;
            elements.analyzeButton.textContent = "Analyse en cours…";
        }
    }

    function showResults() {
        setHidden(elements.loadingState, true);
        setHidden(elements.emptyState, true);
        setHidden(elements.resultsSection, false);
    }

    function restoreButton() {
        if (elements.analyzeButton) {
            elements.analyzeButton.disabled = false;
            elements.analyzeButton.textContent = defaultButtonText;
        }
    }

    function renderSummary(
        payload,
        riskData,
        licenseData,
        maintainabilityData,
        signalsData
    ) {
        const risk = riskData?.risk || {};
        const licenses =
            licenseData?.licenses ||
            riskData?.licenses ||
            [];

        const activity = maintainabilityData?.activity || {};
        const signalSummary = extractSignals(signalsData);

        setText(
            elements.resultPackageName,
            `${payload.name} ${payload.version}`
        );

        setText(
            elements.resultPackageMeta,
            `Écosystème ${payload.ecosystem}`
        );

        setText(
            elements.riskScore,
            risk.score !== undefined
                ? String(risk.score)
                : null
        );

        setText(
            elements.riskLevel,
            risk.level_label || risk.level || "Indisponible"
        );
        applyLevel(elements.riskLevel, risk.level);

        setText(
            elements.vulnerabilityCount,
            formatNumber(riskData?.vulnerability_count)
        );

        setText(
            elements.licenseValue,
            licenses.length > 0
                ? licenses.join(", ")
                : "Non détectée"
        );

        if (!licenseData) {
            setText(elements.licenseStatus, "Analyse indisponible");
        } else if (licenseData.is_deprecated) {
            setText(elements.licenseStatus, "Version obsolète");
        } else if (licenses.length > 0) {
            setText(elements.licenseStatus, "Licence détectée");
        } else {
            setText(elements.licenseStatus, "Aucune licence déclarée");
        }

        setText(
            elements.activityScore,
            activity.score !== null &&
                activity.score !== undefined
                ? `${activity.score} / ${activity.max_score || 10}`
                : null
        );

        setText(
            elements.activityLevel,
            activity.label || "Indisponible"
        );
        applyLevel(elements.activityLevel, activity.level);

        setText(
            elements.signalCount,
            formatNumber(signalSummary.count)
        );

        setText(
            elements.signalLevel,
            signalSummary.level
        );
        applyLevel(elements.signalLevel, signalSummary.level);
    }

    function renderRisk(riskData) {
        const risk = riskData?.risk || {};
        const breakdown = risk.breakdown || {};
        const severityCounts = risk.severity_counts || {};

        setText(elements.riskVulnerabilityPoints, breakdown.vulnerabilities, "0");
        setText(elements.riskLicensePoints, breakdown.license, "0");
        setText(elements.riskDeprecationPoints, breakdown.deprecation, "0");
        setText(elements.riskAgePoints, breakdown.age, "0");
        setText(elements.riskMetadataPoints, breakdown.metadata, "0");

        setText(elements.severityCritical, severityCounts.critical, "0");
        setText(elements.severityHigh, severityCounts.high, "0");
        setText(elements.severityModerate, severityCounts.moderate, "0");
        setText(elements.severityLow, severityCounts.low, "0");
        setText(elements.severityUnknown, severityCounts.unknown, "0");

        if (!elements.riskReasons) return;

        elements.riskReasons.replaceChildren();

        const reasons = Array.isArray(risk.reasons)
            ? risk.reasons
            : [];

        if (reasons.length === 0) {
            const item = createElement(
                "li",
                "",
                riskData
                    ? "Aucun signal de risque majeur détecté."
                    : "Analyse du risque indisponible."
            );

            elements.riskReasons.appendChild(item);
            return;
        }

        reasons.forEach((reason) => {
            elements.riskReasons.appendChild(
                createElement("li", "", reason)
            );
        });
    }

    function renderVulnerabilities(riskData) {
        if (!elements.vulnerabilitiesList) return;

        elements.vulnerabilitiesList.replaceChildren();

        const vulnerabilities = Array.isArray(
            riskData?.vulnerabilities
        )
            ? riskData.vulnerabilities
            : [];

        if (vulnerabilities.length === 0) {
            elements.vulnerabilitiesList.appendChild(
                createElement(
                    "p",
                    "empty-message",
                    riskData
                        ? "Aucune vulnérabilité connue détectée."
                        : "Analyse des vulnérabilités indisponible."
                )
            );
            return;
        }

        const displayedVulnerabilities =
            vulnerabilities.slice(0, 10);

        displayedVulnerabilities.forEach((vulnerability) => {
            const card = createElement("article", "result-item");
            const header = createElement(
                "div",
                "result-item-header"
            );

            const identifier =
                typeof vulnerability.id === "string"
                   ? vulnerability.id
                   : "Vulnérabilité";

            const rawSeverity =
                vulnerability.database_specific?.severity ??
                vulnerability.severity;

            const severity =
                typeof rawSeverity === "string"
                    ? rawSeverity
                    : "INCONNUE";

            header.appendChild(
                createElement("h4", "", identifier)
            );

            const severityBadge = createElement(
                "span",
                "status-badge",
                severity
            );
            severityBadge.dataset.level =
                normalizeLevel(severity);

            header.appendChild(severityBadge);
            card.appendChild(header);

            card.appendChild(
                createElement(
                    "p",
                    "",
                    vulnerability.summary ||
                        "Aucun résumé disponible."
                )
            );

            const aliases = Array.isArray(
                vulnerability.aliases
            )
                ? vulnerability.aliases
                : [];

            if (aliases.length > 0) {
                card.appendChild(
                    createElement(
                        "p",
                        "result-item-meta",
                        `Références : ${aliases.join(", ")}`
                    )
                );
            }

            elements.vulnerabilitiesList.appendChild(card);
        });

        if (vulnerabilities.length > displayedVulnerabilities.length) {
            elements.vulnerabilitiesList.appendChild(
                createElement(
                    "p",
                    "list-notice",
                    `${vulnerabilities.length - displayedVulnerabilities.length} autre(s) vulnérabilité(s) figurent dans la réponse complète de l’API.`
                )
            );
        }
    }

    function renderMaintainability(data) {
        const project = data?.project;
        const scorecard = data?.scorecard || {};

        setText(
            elements.projectName,
            project?.id || "Dépôt non identifié"
        );

        setText(
            elements.projectStars,
            formatNumber(project?.stars_count)
        );

        setText(
            elements.projectIssues,
            formatNumber(project?.open_issues_count)
        );

        setText(
            elements.scorecardScore,
            scorecard.overall_score !== null &&
                scorecard.overall_score !== undefined
                ? `${scorecard.overall_score} / 10`
                : "Indisponible"
        );
    }

    function extractSignals(data) {
        if (!data) {
            return {
                signals: [],
                count: null,
                level: "Indisponible",
            };
        }

        let signals =
            data.signals ||
            data.suspicious_signals ||
            data.findings ||
            data.indicators ||
            [];

        if (!Array.isArray(signals)) {
            signals = [];
        }

        const risk = data.risk || {};
        const count =
            data.signal_count ??
            data.suspicious_signal_count ??
            data.count ??
            signals.length;

        const level =
            data.level_label ||
            data.risk_level_label ||
            risk.level_label ||
            data.level ||
            data.risk_level ||
            risk.level ||
            (Number(count) > 0 ? "À vérifier" : "Faible");

        return {
            signals,
            count,
            level,
        };
    }

    function renderSignals(data) {
        if (!elements.signalsList) return;

        elements.signalsList.replaceChildren();

        const summary = extractSignals(data);

        if (summary.signals.length === 0) {
            elements.signalsList.appendChild(
                createElement(
                    "p",
                    "empty-message",
                    data
                        ? "Aucun comportement suspect détecté."
                        : "Analyse des signaux indisponible."
                )
            );
            return;
        }

        summary.signals.forEach((signal, index) => {
            const card = createElement("article", "result-item");

            if (typeof signal === "string") {
                card.appendChild(
                    createElement(
                        "h4",
                        "",
                        `Signal ${index + 1}`
                    )
                );
                card.appendChild(
                    createElement("p", "", signal)
                );
            } else {
                const title =
                    signal.label ||
                    signal.title ||
                    signal.type ||
                    signal.name ||
                    `Signal ${index + 1}`;

                const description =
                    signal.description ||
                    signal.reason ||
                    signal.message ||
                    signal.summary ||
                    "Information complémentaire indisponible.";

                card.appendChild(
                    createElement("h4", "", title)
                );
                card.appendChild(
                    createElement("p", "", description)
                );

                const level =
                    signal.level_label ||
                    signal.severity ||
                    signal.level;

                if (level) {
                    const badge = createElement(
                        "span",
                        "status-badge",
                        level
                    );
                    badge.dataset.level =
                        normalizeLevel(level);
                    card.appendChild(badge);
                }
            }

            elements.signalsList.appendChild(card);
        });
    }

    elements.form.addEventListener("submit", async (event) => {
        event.preventDefault();
        setError();

        const payload = {
            ecosystem: elements.ecosystem?.value.trim(),
            name: elements.packageName?.value.trim(),
            version: elements.packageVersion?.value.trim(),
        };

        if (
            !payload.ecosystem ||
            !payload.name ||
            !payload.version
        ) {
            setError(
                "Renseigne l’écosystème, le nom du paquet et sa version."
            );
            return;
        }

        showLoading();

        const endpointEntries = Object.entries(endpoints);

        try {
            const settledResults = await Promise.allSettled(
                endpointEntries.map(([, endpoint]) =>
                    postAnalysis(endpoint, payload)
                )
            );

            const results = {};
            const failures = [];

            settledResults.forEach((result, index) => {
                const analysisName = endpointEntries[index][0];

                if (result.status === "fulfilled") {
                    results[analysisName] = result.value;
                } else {
                    failures.push({
                        name: analysisName,
                        message: result.reason?.message,
                    });
                }
            });

            if (Object.keys(results).length === 0) {
                throw new Error(
                    failures[0]?.message ||
                        "Aucune analyse n’a pu être effectuée."
                );
            }

            renderSummary(
                payload,
                results.risk,
                results.licenses,
                results.maintainability,
                results.signals
            );

            renderRisk(results.risk);
            renderVulnerabilities(results.risk);
            renderMaintainability(results.maintainability);
            renderSignals(results.signals);

            if (failures.length > 0) {
                setError(
                    "Certaines informations sont temporairement indisponibles. Les autres résultats restent affichés."
                );
            }

            showResults();

            elements.resultsSection?.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        } catch (error) {
            setHidden(elements.loadingState, true);
            setHidden(elements.resultsSection, true);
            setHidden(elements.emptyState, false);

            setError(
                error.message ||
                    "Une erreur est survenue pendant l’analyse."
            );
        } finally {
            restoreButton();
        }
    });

    elements.newAnalysisButton?.addEventListener("click", () => {
        elements.form.reset();
        setError();

        setHidden(elements.resultsSection, true);
        setHidden(elements.loadingState, true);
        setHidden(elements.emptyState, false);

        elements.form.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });

        elements.packageName?.focus();
    });

    const exampleButtons = document.querySelectorAll(
        "[data-example], [data-ecosystem][data-name][data-version]"
    );

    exampleButtons.forEach((button) => {
        button.addEventListener("click", () => {
            let ecosystem =
                button.dataset.exampleEcosystem ||
                button.dataset.ecosystem;
            let name =
                button.dataset.exampleName ||
                button.dataset.packageName ||
                button.dataset.name;
            let version =
                button.dataset.exampleVersion ||
                button.dataset.version;

            if (
                button.dataset.example &&
                (!ecosystem || !name || !version)
            ) {
                const values =
                    button.dataset.example.split("|");

                [ecosystem, name, version] = values;
            }

            if (ecosystem && elements.ecosystem) {
                elements.ecosystem.value = ecosystem;
            }

            if (name && elements.packageName) {
                elements.packageName.value = name;
            }

            if (version && elements.packageVersion) {
                elements.packageVersion.value = version;
            }

            if (ecosystem && name && version) {
                elements.form.requestSubmit();
            }
        });
    });
});