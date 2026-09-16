"""Documentation contracts for repository command scripts."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SECTIONS = (
    "## Purpose",
    "## Requirements",
    "## Commands",
    "## Options",
    "## Output and exit status",
    "## Safety and operational notes",
    "## Troubleshooting",
)


def test_each_command_script_has_a_complete_guide():
    script_paths = sorted(
        path
        for path in (ROOT / "scripts").glob("*.py")
        if path.name != "__init__.py"
    )

    for script_path in script_paths:
        guide_path = ROOT / "docs" / f"guide_{script_path.stem}.md"
        assert guide_path.is_file(), f"missing guide for {script_path.name}"
        guide = guide_path.read_text(encoding="utf-8")
        assert guide.startswith(f"# `{script_path.name}` guide\n")
        assert f"python3 scripts/{script_path.name}" in guide
        for section in REQUIRED_SECTIONS:
            assert section in guide, f"{guide_path.name} is missing {section}"


def test_no_orphan_script_guides_exist():
    script_stems = {
        path.stem
        for path in (ROOT / "scripts").glob("*.py")
        if path.name != "__init__.py"
    }
    guide_stems = {
        path.stem[len("guide_") :]
        for path in (ROOT / "docs").glob("guide_*.md")
    }

    assert guide_stems == script_stems
