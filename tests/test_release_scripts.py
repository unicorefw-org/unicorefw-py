"""Tests for release gates and artifact metadata generation."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import pytest

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


def test_release_metadata_contains_artifact_hashes_and_sbom(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    output_dir = tmp_path / "release-metadata"
    dist_dir.mkdir()
    wheel_path = dist_dir / "unicorefw-2.3.4-py3-none-any.whl"
    source_path = dist_dir / "unicorefw-2.3.4.tar.gz"
    wheel_path.write_bytes(b"wheel fixture")
    source_path.write_bytes(b"source fixture")

    build_metadata(dist_dir, output_dir, "v2.3.4")

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
    assert "needs: quality" in workflow
    assert "needs: build" in workflow


def test_test_workflow_enforces_branch_coverage_ratchet():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )
    threshold_match = re.search(r"--cov-fail-under=(\d+(?:\.\d+)?)", workflow)

    assert "name: Branch coverage ratchet" in workflow
    assert "--cov-branch" in workflow
    assert "--cov-report=term-missing" in workflow
    assert "--cov-report=xml" in workflow
    assert "--cov-report=json" in workflow
    assert threshold_match is not None
    assert 73 <= float(threshold_match.group(1)) <= 100
