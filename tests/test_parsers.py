from app.services.requirements_parser import parse_requirements_txt
from pathlib import Path

from app.services.package_lock_parser import parse_package_lock

def test_parse_requirements_txt() -> None:
    content = """
requests==2.19.0
jinja2==2.10
urllib3==1.24.1
"""

    dependencies = parse_requirements_txt(content)

    assert [dependency.model_dump() for dependency in dependencies] == [
        {
            "ecosystem": "PyPI",
            "name": "requests",
            "version": "2.19.0",
        },
        {
            "ecosystem": "PyPI",
            "name": "jinja2",
            "version": "2.10",
        },
        {
            "ecosystem": "PyPI",
            "name": "urllib3",
            "version": "1.24.1",
        },
    ]
def test_parse_package_lock() -> None:
    content = Path(
        "samples/package-lock-vulnerable.json"
    ).read_text(encoding="utf-8")

    dependencies = parse_package_lock(content)

    assert [dependency.model_dump() for dependency in dependencies] == [
        {
            "ecosystem": "npm",
            "name": "axios",
            "version": "0.21.1",
        },
        {
            "ecosystem": "npm",
            "name": "lodash",
            "version": "4.17.15",
        },
        {
            "ecosystem": "npm",
            "name": "minimist",
            "version": "1.2.5",
        },
    ]
