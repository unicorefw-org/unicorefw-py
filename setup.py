from setuptools import setup, find_packages

setup(
    name="unicorefw",  # Name of the library
    version="1.0.2",   # version of the library
    author="Kenny Ngo",
    author_email="kenny@unicorefw.org",
    description="A versatile Python library for utility functions similar to Underscore.js",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="BSD-3-Clause",
    url="https://github.com/unicorefw-org/unicorefw-py",  # GitHub repo or project page
    packages=find_packages("src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    py_modules=["unicorefw"],
    exclude=["examples", "tests", "utils", "benchmark", "docs"],
    python_requires=">=3.6",
    install_requires=[  
        # List dependencies here
    ],
)
