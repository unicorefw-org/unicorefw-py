#!/usr/bin/env python3
"""Verify that a release tag agrees with package metadata and the changelog."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_TAG_RE = re.compile(
    r"^v(?P<version>0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def fail(message: str) -> NoReturn:
    raise SystemExit(f"release verification failed: {message}")


def read_version(metadata_path: Path) -> str:
    """Read a literal VERSION assignment without importing the package."""
    tree = ast.parse(metadata_path.read_text(encoding="utf-8"), metadata_path.name)
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "VERSION"
            for target in statement.targets
        ):
            continue
        if isinstance(statement.value, ast.Constant) and isinstance(
            statement.value.value, str
        ):
            return statement.value.value
        fail("VERSION must be a string literal")
    fail("VERSION was not found in unicorefw/_metadata.py")


def verify_release(tag: str, root: Path = ROOT) -> str:
    """Return the validated version or terminate with a precise error."""
    tag_match = SEMANTIC_TAG_RE.fullmatch(tag)
    if tag_match is None:
        fail(f"tag {tag!r} is not a supported semantic version tag")

    tag_version = tag[1:]
    metadata_version = read_version(root / "unicorefw" / "_metadata.py")
    if tag_version != metadata_version:
        fail(
            f"tag version {tag_version!r} does not match package version "
            f"{metadata_version!r}"
        )

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    release_heading = re.compile(
        rf"^## \[{re.escape(tag_version)}\](?:\s|$)",
        flags=re.MULTILINE,
    )
    if release_heading.search(changelog) is None:
        fail(f"CHANGELOG.md has no release heading for version {tag_version!r}")
    return tag_version


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        fail("usage: verify_release.py vMAJOR.MINOR.PATCH")
    version = verify_release(argv[1])
    print(f"release metadata verified for {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
