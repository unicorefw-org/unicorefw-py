"""
Setup script for UniCoreFW package.
"""
from pathlib import Path
from runpy import run_path

from setuptools import find_packages, setup

ROOT = Path(__file__).resolve().parent
METADATA = run_path(str(ROOT / "unicorefw" / "_metadata.py"))
long_description = (ROOT / "README.md").read_text(encoding="utf-8")

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
    packages=find_packages(exclude=("examples", "tests")),
    python_requires=">=3.7",
    install_requires=[],
)
