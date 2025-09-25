"""Setup script for dd_ie package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="dd_ie",
    version="1.0.0",
    author="DD_IE Contributors",
    description="Double demeaning technique for unbiased estimation of interactions in fixed effects models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/[username]/[repository]",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "linearmodels>=4.0.0",
    ],
    extras_require={
        "viz": ["matplotlib>=3.5.0", "seaborn>=0.11.0"],
        "dev": ["pytest>=6.0", "pytest-cov", "black", "flake8"],
    },
    keywords="econometrics, fixed effects, interactions, panel data, double demeaning",
    project_urls={
        "Bug Reports": "https://github.com/[username]/[repository]/issues",
        "Source": "https://github.com/[username]/[repository]",
        "Documentation": "https://github.com/[username]/[repository]#readme",
    },
)
