"""Tests for deterministic distribution build hooks."""

from __future__ import annotations

import os
import runpy
import subprocess
import sys
from distutils.errors import DistutilsExecError
from pathlib import Path
from unittest.mock import Mock

import pytest
import setuptools
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
from setuptools.dist import Distribution

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def _load_command_classes(monkeypatch):
    setup_arguments = {}
    monkeypatch.setattr(
        setuptools,
        "setup",
        lambda **arguments: setup_arguments.update(arguments),
    )

    runpy.run_path(str(ROOT / "setup.py"))

    return setup_arguments["cmdclass"]


def test_registry_generation_command_uses_fixed_bounded_subprocess(
    monkeypatch,
):
    command_classes = _load_command_classes(monkeypatch)
    runner = Mock()
    monkeypatch.setattr(subprocess, "run", runner)

    command_classes["generate_core_registry"](Distribution()).run()

    runner.assert_called_once_with(
        [
            sys.executable,
            "-I",
            str(ROOT / "scripts" / "generate_core_registry.py"),
        ],
        check=True,
        cwd=str(ROOT),
        shell=False,
        timeout=120,
    )


@pytest.mark.parametrize(
    ("command_name", "base_command"),
    (("build_py", build_py), ("sdist", sdist)),
)
def test_distribution_commands_generate_registry_before_building(
    monkeypatch,
    command_name,
    base_command,
):
    command_classes = _load_command_classes(monkeypatch)
    events = []
    command = command_classes[command_name](Distribution())
    monkeypatch.setattr(
        command,
        "run_command",
        lambda name: events.append(("generate", name)),
    )
    monkeypatch.setattr(
        base_command,
        "run",
        lambda self: events.append(("build", command_name)),
    )

    command.run()

    assert events == [
        ("generate", "generate_core_registry"),
        ("build", command_name),
    ]


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    (
        (
            subprocess.CalledProcessError(7, ["private-command"]),
            "core registry generation failed with exit code 7",
        ),
        (
            subprocess.TimeoutExpired(["private-command"], 120),
            "core registry generation timed out",
        ),
        (OSError("private-path"), "core registry generation could not start"),
    ),
)
def test_registry_generation_command_fails_closed_without_disclosing_command(
    monkeypatch,
    failure,
    expected_message,
):
    command_classes = _load_command_classes(monkeypatch)

    def fail_run(*args, **kwargs):
        raise failure

    monkeypatch.setattr(subprocess, "run", fail_run)

    with pytest.raises(DistutilsExecError) as caught:
        command_classes["generate_core_registry"](Distribution()).run()

    assert str(caught.value) == expected_message
    assert "private" not in str(caught.value)
