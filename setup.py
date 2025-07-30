#!/usr/bin/env python3
"""Setup script for langgraph-chrome-tools package."""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    """Read README.md for long description."""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Read requirements from requirements.txt
def read_requirements():
    """Read requirements from requirements.txt."""
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

setup(
    name="langgraph-chrome-tools",
    version="0.1.0",
    author="LangGraph Chrome Tools Team",
    author_email="support@langgraph-chrome-tools.com",
    description="LangGraph tools for Chrome automation using Playwright",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/langgraph-chrome-tools",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.23.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "langgraph-chrome-setup=langgraph_chrome_tools.cli:setup_command",
            "langgraph-chrome-install=langgraph_chrome_tools.cli:install_playwright",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="langgraph, playwright, chrome, automation, ai, tools",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/langgraph-chrome-tools/issues",
        "Source": "https://github.com/yourusername/langgraph-chrome-tools",
        "Documentation": "https://langgraph-chrome-tools.readthedocs.io/",
    },
)