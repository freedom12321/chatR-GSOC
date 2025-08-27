#!/usr/bin/env python3
"""Setup script for ChatR."""

from setuptools import setup, find_packages
import os

# Read the README file
with open("readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="chatr",
    version="0.1.0",
    author="ChatR Team",
    description="An intelligent, local assistant for R programmers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/chatR-GSOC",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "chatr=chatr.cli.main:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)