from app.services.risk_score import calculate_risk_score
from app.services.severity import calculate_vulnerability_points


def test_vulnerability_points_are_weighted() -> None:
    severity_counts = {
        "critical": 0,
        "high": 1,
        "moderate": 4,
        "low": 0,
        "unknown": 5,
    }

    assert calculate_vulnerability_points(severity_counts) == 55


def test_vulnerability_points_are_capped() -> None:
    severity_counts = {
        "critical": 3,
        "high": 3,
        "moderate": 3,
        "low": 3,
        "unknown": 3,
    }

    assert calculate_vulnerability_points(severity_counts) == 55


def test_risk_score_for_vulnerable_old_package() -> None:
    result = calculate_risk_score(
        vulnerability_count=10,
        severity_counts={
            "critical": 0,
            "high": 1,
            "moderate": 4,
            "low": 0,
            "unknown": 5,
        },
        licenses=["Apache-2.0"],
        is_deprecated=False,
        published_at="2018-06-12T14:46:15Z",
        metadata_status="found",
        links=[],
        related_projects=[],
    )

    assert result["score"] == 70
    assert result["level"] == "high"
    assert result["score_version"] == "1.1"
    assert result["breakdown"]["vulnerabilities"] == 55