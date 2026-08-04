"""Minimal packaging so users can `pip install -e .` for local dev,
or `pip install knowme` once we publish to PyPI.

We keep this trivial — no test-requires, no extras — because KnowMe is
intentionally zero-runtime-deps. `pyyaml` is an optional soft dep loaded
only if the user has a config file.
"""
from setuptools import setup, find_packages

setup(
    name="knowme",
    version="0.1.0",
    description="Cross-agent activity trace — record what any AI agent just did.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="linxun",
    python_requires=">=3.10",
    packages=find_packages(exclude=["tests", "tests.*"]),
    entry_points={
        "console_scripts": [
            "knowme=knowme.cli:main",
        ],
    },
    extras_require={
        # Only needed if user creates ~/.knowme/config.yaml
        "yaml": ["pyyaml>=6.0"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ],
    include_package_data=True,
    package_data={
        # Ship the skill definition with the package so users can `cp $(python -c ...) ~/.claude/skills/`
        "knowme": ["../skills/knowme/SKILL.md"],
    },
)
