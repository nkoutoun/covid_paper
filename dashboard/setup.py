"""Setup script for COVID-19 Belgium Dashboard."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="covid-belgium-dashboard",
    version="1.0.0",
    author="COVID-19 Belgium Dashboard Contributors",
    description="Interactive dashboard for COVID-19 data analysis in Belgian municipalities",
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
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "plotly>=5.0.0",
        "dash>=2.0.0",
        "geopandas>=0.10.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "jupyter>=1.0.0",
            "notebook>=6.0.0",
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
        ],
    },
    entry_points={
        "console_scripts": [
            "covid-dashboard=dashboard.main:main",
        ],
    },
    keywords="covid-19, belgium, dashboard, visualization, epidemiology, municipalities",
    project_urls={
        "Bug Reports": "https://github.com/[username]/[repository]/issues",
        "Source": "https://github.com/[username]/[repository]", 
        "Documentation": "https://github.com/[username]/[repository]#readme",
    },
    include_package_data=True,
    package_data={
        "dashboard": [
            "data/*.xlsx", 
            "data_public/shapefiles/*",
        ],
    },
)
