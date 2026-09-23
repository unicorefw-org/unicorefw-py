"""Tests for release gates and artifact metadata generation."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from scripts.build_release_metadata import build_metadata
from scripts.verify_release import read_version, verify_release
from scripts.verify_wheel import inspect_wheel

ROOT = Path(__file__).resolve().parents[1]


def _write_release_fixture(root: Path, version: str, changelog: str) -> None:
    package_dir = root / "unicorefw"
    package_dir.mkdir()
    (package_dir / "_metadata.py").write_text(
        f'VERSION = "{version}"\n', encoding="utf-8"
    )
    (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")


def test_release_verifier_requires_tag_metadata_and_changelog_agreement(
    tmp_path: Path,
):
    _write_release_fixture(
        tmp_path,
        "2.3.4",
        "# Changelog\n\n## [2.3.4] - 2026-07-18\n",
    )

    assert read_version(tmp_path / "unicorefw" / "_metadata.py") == "2.3.4"
    assert verify_release("v2.3.4", root=tmp_path) == "2.3.4"


@pytest.mark.parametrize(
    ("tag", "version", "changelog"),
    [
        ("2.3.4", "2.3.4", "## [2.3.4]\n"),
        ("v2.3.5", "2.3.4", "## [2.3.5]\n"),
        ("v2.3.4", "2.3.4", "## [Unreleased]\n"),
    ],
)
def test_release_verifier_rejects_inconsistent_inputs(
    tmp_path: Path,
    tag: str,
    version: str,
    changelog: str,
):
    _write_release_fixture(tmp_path, version, changelog)

    with pytest.raises(SystemExit, match="release verification failed"):
        verify_release(tag, root=tmp_path)


def test_release_metadata_contains_artifact_hashes_and_sbom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dist_dir = tmp_path / "dist"
    output_dir = tmp_path / "release-metadata"
    dist_dir.mkdir()
    wheel_path = dist_dir / "unicorefw-2.3.4-py3-none-any.whl"
    source_path = dist_dir / "unicorefw-2.3.4.tar.gz"
    wheel_path.write_bytes(b"wheel fixture")
    source_path.write_bytes(b"source fixture")

    def unsupported_write_text(*args, **kwargs):
        raise AssertionError("Path.write_text() is unavailable to this code path")

    monkeypatch.setattr(Path, "write_text", unsupported_write_text)

    build_metadata(dist_dir, output_dir, "v2.3.4")

    checksum_bytes = (output_dir / "SHA256SUMS").read_bytes()
    assert checksum_bytes.endswith(b"\n")
    assert b"\r\n" not in checksum_bytes
    checksum_lines = (
        (output_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    )
    assert checksum_lines == [
        f"{hashlib.sha256(wheel_path.read_bytes()).hexdigest()}  {wheel_path.name}",
        f"{hashlib.sha256(source_path.read_bytes()).hexdigest()}  {source_path.name}",
    ]
    manifest = json.loads(
        (output_dir / "release-manifest.json").read_text(encoding="utf-8")
    )
    sbom = json.loads((output_dir / "sbom.cdx.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "2.3.4"
    assert len(manifest["artifacts"]) == 2
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["metadata"]["component"]["purl"] == "pkg:pypi/unicorefw@2.3.4"


def test_wheel_inspector_rejects_path_traversal(tmp_path: Path):
    wheel_path = tmp_path / "unsafe.whl"
    with zipfile.ZipFile(wheel_path, "w") as archive:
        archive.writestr("../outside.py", "unsafe")

    with pytest.raises(SystemExit, match="unsafe path"):
        inspect_wheel(wheel_path)


def test_wheel_inspector_rejects_repository_release_tooling(tmp_path: Path):
    wheel_path = tmp_path / "tooling.whl"
    with zipfile.ZipFile(wheel_path, "w") as archive:
        archive.writestr("scripts/__init__.py", "")

    with pytest.raises(SystemExit, match="release tooling"):
        inspect_wheel(wheel_path)


def test_release_workflow_has_no_floating_action_or_password_publish():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    external_action_lines = [
        line.strip()
        for line in workflow.splitlines()
        if "uses:" in line and "uses: ./" not in line
    ]

    assert external_action_lines
    assert all(
        re.search(r"@[0-9a-f]{40}(?:\s+#\s+v[^\s]+)?$", line)
        for line in external_action_lines
    )
    assert "PYPI_PASSWORD" not in workflow
    assert "TWINE_PASSWORD" not in workflow
    assert "id-token: write" in workflow
    assert "uses: ./.github/workflows/codeql.yml" in workflow
    assert "needs: [quality, codeql]" in workflow
    assert "needs: build" in workflow
    assert (
        "pypa/gh-action-pypi-publish@"
        "ba38be9e461d3875417946c167d0b5f3d385a247 # v1.14.1" in workflow
    )


def test_codeql_workflow_is_pinned_and_enforces_material_findings():
    workflow = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(
        encoding="utf-8"
    )
    external_action_lines = [
        line.strip() for line in workflow.splitlines() if "uses:" in line
    ]

    assert external_action_lines
    assert all(
        re.search(r"@[0-9a-f]{40}\s+#\s+v[^\s]+$", line)
        for line in external_action_lines
    )
    assert (
        workflow.count(
            "github/codeql-action/" "init@7211b7c8077ea37d8641b6271f6a365a22a5fbfa"
        )
        == 1
    )
    assert workflow.count("@7211b7c8077ea37d8641b6271f6a365a22a5fbfa # v4.36.0") == 3
    assert "queries: security-extended" in workflow
    assert "upload: ${{ startsWith(github.ref, 'refs/tags/')" in workflow
    assert "!startsWith(github.ref, 'refs/tags/')" in workflow
    assert "verify_security_policy.py sarif" in workflow
    assert "--minimum-severity 4" in workflow
    assert "security-events: write" in workflow


def test_test_workflow_enforces_branch_coverage_ratchet():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    threshold_match = re.search(r"--cov-fail-under=(\d+(?:\.\d+)?)", workflow)
    config_match = re.search(r"fail_under\s*=\s*(\d+(?:\.\d+)?)", pyproject)

    assert "name: Branch coverage ratchet" in workflow
    assert "--cov-branch" in workflow
    assert "--cov-report=term-missing" in workflow
    assert "--cov-report=xml" in workflow
    assert "--cov-report=json" in workflow
    assert "--basetemp=" in workflow
    assert "id-token: write" in workflow
    assert (
        "codecov/codecov-action@0fb7174895f61a3b6b78fc075e0cd60383518dac"
        " # v5.5.5" in workflow
    )
    assert "files: ./coverage.xml" in workflow
    assert "slug: unicorefw-org/unicorefw-py" in workflow
    assert "token: ${{ secrets.CODECOV_TOKEN }}" in workflow
    assert "use_oidc: true" in workflow
    assert threshold_match is not None
    assert config_match is not None
    assert 77 <= float(threshold_match.group(1)) <= 100
    assert float(config_match.group(1)) == float(threshold_match.group(1))
    assert float(threshold_match.group(1)) == 83.0


def test_ci_uses_fixed_tooling_without_dropping_legacy_python_support():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )
    release_workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "\"pip>=26.1.2,<27; python_version >= '3.10'\"" in workflow
    assert workflow.count('"pip>=26.1.2,<27"') == 5
    assert '"pip>=26.1.2,<27"' in release_workflow
    assert "\"pytest>=7.4,<9; python_version < '3.10'\"" in workflow
    assert "\"pytest>=9.0.3,<10; python_version >= '3.10'\"" in workflow
    assert '"setuptools>=83,<84"' in workflow
    assert "python -m pip_audit --strict" in workflow
    assert "setuptools>=61,<83; python_version < '3.10'" in pyproject
    assert "setuptools>=83,<84; python_version >= '3.10'" in pyproject


def test_security_job_scans_secrets_and_enforces_suppression_expiry():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )

    assert '"detect-secrets==1.5.0"' in workflow
    assert "verify_security_policy.py suppressions --root ." in workflow
    assert "git ls-files --cached --others --exclude-standard -z |" in workflow
    assert "xargs -0 detect-secrets-hook --no-verify" in workflow
    assert "tests/test_security_policy.py" in workflow
    assert "tests/test_cache_manager_security.py" in workflow


def test_ci_enforces_root_import_budget_and_records_submodules():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )

    assert "name: Root import budget" in workflow
    assert "runs-on: ubuntu-24.04" in workflow
    assert 'python-version: "3.11.9"' in workflow
    assert 'python -m pip install "."' in workflow
    assert "python scripts/benchmark_imports.py unicorefw" in workflow
    assert "--forbid-optional" in workflow
    assert "--max-median-ms 100" in workflow
    assert "--max-median-rss-kib 10240" in workflow
    assert "unicorefw.core" in workflow
    assert "Record installed optional import measurements" in workflow
    assert "Record representative collection measurements" in workflow
    assert "python scripts/benchmark_collections.py" in workflow
    assert "Verify generated core registry" in workflow
    assert "python scripts/generate_core_registry.py --check" in workflow
    assert "Record dispatch measurements" in workflow
    assert "python scripts/benchmark_dispatch.py" in workflow
    assert "--runs 7" in workflow
    assert "--iterations 100000" in workflow
    assert "--runs 5" in workflow
    assert "--size 4000" in workflow


def test_source_distribution_includes_generated_api_metadata():
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")

    assert "recursive-include docs/api *.json" in manifest


def test_optional_extras_and_ci_use_supported_bounded_dependency_lines():
    setup_source = (ROOT / "setup.py").read_text(encoding="utf-8")
    setup_tree = ast.parse(setup_source)
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )

    setup_call = next(
        node
        for node in ast.walk(setup_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setup"
    )
    extras_keyword = next(
        keyword for keyword in setup_call.keywords if keyword.arg == "extras_require"
    )
    extras = ast.literal_eval(extras_keyword.value)

    assert 'run_path(str(ROOT / "unicorefw" / "_metadata.py"))' in setup_source
    assert not any(
        (
            isinstance(node, ast.Import)
            and any(alias.name == "unicorefw" for alias in node.names)
        )
        or (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("unicorefw")
        )
        for node in ast.walk(setup_tree)
    )
    assert extras["crypto"] == [
        "cryptography>=44.0.3,<45; python_version < '3.8'",
        (
            "cryptography>=46.0.7,<47; python_version >= '3.8' "
            "and python_version < '3.9'"
        ),
        "cryptography>=49,<50; python_version >= '3.9'",
    ]
    assert extras["orm"] == ["SQLAlchemy[asyncio]>=2.0.51,<2.1"]
    assert extras["core"] == []
    assert extras["database"] == [
        "psycopg2-binary>=2.9.12,<2.10; python_version >= '3.9'",
        "PyMySQL[rsa]>=1.2,<1.3; python_version >= '3.9'",
        "pymongo>=4.17,<5; python_version >= '3.9'",
        ("redis>=7.4.1,<8; python_version >= '3.9' " "and python_version < '3.10'"),
        "redis>=8.0.1,<9; python_version >= '3.10'",
    ]
    assert extras["spreadsheet"] == [
        "pandas>=2.0,<3; python_version >= '3.9'",
        "openpyxl>=3.1.5,<4; python_version >= '3.9'",
        "defusedxml>=0.7.1,<1; python_version >= '3.9'",
    ]
    assert workflow.count('".[crypto,orm]"') == 1
    assert workflow.count('".[crypto,orm,spreadsheet]"') == 2
    assert workflow.count('".[database]"') == 1
    assert "tests/test_crypto.py" in workflow
    assert "tests/test_db_lifecycle.py" in workflow
    assert "tests/test_db_thread_ownership.py" in workflow
    assert "tests/test_orm.py" in workflow


def test_database_integration_uses_pinned_services_and_bounded_drivers():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )

    assert "name: PostgreSQL and MySQL integration" in workflow
    assert re.search(
        r"image: postgres:17\.10@sha256:[0-9a-f]{64}$",
        workflow,
        re.MULTILINE,
    )
    assert re.search(
        r"image: mysql:8\.4\.10@sha256:[0-9a-f]{64}$",
        workflow,
        re.MULTILINE,
    )
    assert '".[database]"' in workflow
    assert "import psycopg2, pymongo, pymysql, redis" in workflow
    assert "benchmark_imports.py unicorefw.db --runs 3" in workflow
    assert "python -m pip_audit --strict" in workflow
    assert "tests/test_db_service_integration.py" in workflow
    assert 'UNICORE_FW_DATABASE_INTEGRATION: "1"' in workflow
