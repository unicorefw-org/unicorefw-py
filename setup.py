"""
Setup script for UniCoreFW package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="unicorefw",
    version="1.0.4",
    author="Kenny Ngo",
    author_email="kenny@unicorefw.org",
    description="Universal Core Utility Library",
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
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    py_modules=["unicorefw"],    
    package_dir={"": "."},
    exclude=["examples", "tests", "utils", "benchmark", "docs"],    
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
)
