"""
Setup script for UniCoreFW package.
"""
import subprocess
import sys
from distutils.errors import DistutilsExecError
from pathlib import Path
from runpy import run_path

from setuptools import Command, find_packages, setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist

ROOT = Path(__file__).resolve().parent
METADATA = run_path(str(ROOT / "unicorefw" / "_metadata.py"))
long_description = (ROOT / "README.md").read_text(encoding="utf-8")


class GenerateCoreRegistry(Command):
    """Generate deterministic API declarations before packaging."""

    description = "generate deterministic UniCoreFW API declarations"
    user_options = []

    def initialize_options(self):
        pass

    finalize_options = initialize_options

    def run(self):
        command = [
            sys.executable,
            "-I",
            str(ROOT / "scripts" / "generate_core_registry.py"),
        ]
        try:
            subprocess.run(
                command,
                check=True,
                cwd=str(ROOT),
                shell=False,
                timeout=120,
            )
        except subprocess.CalledProcessError as exc:
            raise DistutilsExecError(
                f"core registry generation failed with exit code {exc.returncode}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise DistutilsExecError("core registry generation timed out") from exc
        except OSError as exc:
            raise DistutilsExecError(
                "core registry generation could not start"
            ) from exc


class BuildPyWithCoreRegistry(_build_py):
    """Generate declarations before copying wheel package modules."""

    def run(self):
        self.run_command("generate_core_registry")
        super().run()


class SdistWithCoreRegistry(_sdist):
    """Generate declarations before archiving source distributions."""

    def run(self):
        self.run_command("generate_core_registry")
        super().run()


setup(
    name=METADATA["PACKAGE_NAME"],
    version=METADATA["VERSION"],
    author=METADATA["AUTHOR"],
    author_email=METADATA["AUTHOR_EMAIL"],
    description="UniCoreFW is a lodash/underscore-style utility toolkit for Python with both functional and chainable APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/unicorefw-org/unicorefw-py",
    project_urls={
        "Bug Tracker": "https://github.com/unicorefw-org/unicorefw-py/issues",
        "Documentation": "https://unicorefw.org/docs.html",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    license="BSD-3-Clause",
    cmdclass={
        "build_py": BuildPyWithCoreRegistry,
        "generate_core_registry": GenerateCoreRegistry,
        "sdist": SdistWithCoreRegistry,
    },
    packages=find_packages(exclude=("examples", "tests", "scripts", "scripts.*")),
    python_requires=">=3.7",
    install_requires=[],
    extras_require={
        "core": [],
        "crypto": [
            "cryptography>=44.0.3,<45; python_version < '3.8'",
            (
                "cryptography>=46.0.7,<47; python_version >= '3.8' "
                "and python_version < '3.9'"
            ),
            "cryptography>=49,<50; python_version >= '3.9'",
        ],
        "orm": [
            "SQLAlchemy[asyncio]>=2.0.51,<2.1",
        ],
        "database": [
            "psycopg2-binary>=2.9.12,<2.10; python_version >= '3.9'",
            "PyMySQL[rsa]>=1.2,<1.3; python_version >= '3.9'",
            "pymongo>=4.17,<5; python_version >= '3.9'",
            ("redis>=7.4.1,<8; python_version >= '3.9' " "and python_version < '3.10'"),
            "redis>=8.0.1,<9; python_version >= '3.10'",
        ],
        "spreadsheet": [
            "pandas>=2.0,<3; python_version >= '3.9'",
            "openpyxl>=3.1.5,<4; python_version >= '3.9'",
            "defusedxml>=0.7.1,<1; python_version >= '3.9'",
        ],
    },
)
