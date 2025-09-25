"""
Configuration module for COVID-19 Belgium Dashboard

This module contains all configuration settings, paths, and constants
used throughout the dashboard application.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_PUBLIC_DIR = BASE_DIR / "data_public"

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
DATA_PUBLIC_DIR.mkdir(exist_ok=True)
(DATA_PUBLIC_DIR / "shapefiles").mkdir(exist_ok=True)

# Data URLs (automatically downloaded)
DATA_URLS = {
    "covid_cases": "https://epistat.sciensano.be/Data/COVID19BE_CASES_MUNI.csv",
    "vaccination": "https://epistat.sciensano.be/data/COVID19BE_VACC_MUNI_CUM.csv",
    "shapefile_zip": "https://statbel.fgov.be/sites/default/files/files/opendata/Statistische%20sectoren/sh_statbel_statistical_sectors_20190101.shp.zip"
}

# File paths
FILE_PATHS = {
    "covid_cases": DATA_PUBLIC_DIR / "COVID19BE_CASES_MUNI.csv",
    "vaccination": DATA_PUBLIC_DIR / "COVID19BE_VACC_MUNI_CUM.csv",
    "population": DATA_DIR / "population_by_NIS.xlsx",
    "oxford_data": DATA_DIR / "si_be_muni_daily.xlsx",
    "shapefile": DATA_PUBLIC_DIR / "shapefiles" / "sh_statbel_statistical_sectors_20190101.shp",
    "intermediate_data": DATA_DIR / "intermediate_data_covid_gri.csv"
}

# Time period configuration
TIME_PERIODS = {
    "years": [2020, 2021, 2022],
    "weeks_per_year": {2020: 53, 2021: 52, 2022: 52}
}

# Dashboard configuration
DASHBOARD_CONFIG = {
    "host": "127.0.0.1",
    "port": 8050,
    "debug": True,
    "map_center": {"lat": 50.8503, "lon": 4.3517},
    "map_zoom": 6.5,
    "map_height": 700
}

# Variable definitions for dashboard
VARIABLE_OPTIONS = [
    {"label": "🦠 COVID-19 Cases", "value": "CASES"},
    {"label": "📊 Stringency Index", "value": "SI"},
    {"label": "💉 Vaccination %", "value": "vacc_pct"},
    {"label": "👥 Population", "value": "POPULATION"}
]

# Color scales for visualization
COLOR_SCALES = {
    "CASES": "Reds",
    "SI": "Oranges", 
    "vacc_pct": "Greens",
    "POPULATION": "Viridis"
}

# Variable labels and formatting
VARIABLE_LABELS = {
    "CASES": "COVID-19 Cases",
    "SI": "Stringency Index",
    "vacc_pct": "Vaccination %",
    "POPULATION": "Population"
}

HOVER_LABELS = {
    "CASES": "Cases",
    "SI": "Stringency Index (SI)",
    "vacc_pct": "Vaccinations",
    "POPULATION": "Population"
}

# Belgian regions and provinces
REGIONS = ["Flanders", "Wallonia", "Brussels"]
PROVINCES = [
    "Antwerpen", "OostVlaanderen", "VlaamsBrabant", "Limburg", "WestVlaanderen",
    "Hainaut", "Liège", "Luxembourg", "Namur", "BrabantWallon", "Brussels"
]

# Data processing settings
DATA_PROCESSING = {
    "missing_cases_replacement": 1,  # Replace '<5' with 1
    "missing_vacc_replacement": 1,   # Replace '<10' with 1
    "excluded_age_groups": ["0-17"],  # Exclude children from vaccination data
    "included_vaccine_doses": ["B", "C"],  # Only 1st vaccination doses
    "geometry_simplification_tolerance": 0.01,  # For map performance
    "coordinate_system": "EPSG:4326"  # WGS84 for web mapping
}

# Warning and display settings
DISPLAY_SETTINGS = {
    "pandas_max_columns": None,
    "matplotlib_style": "default",
    "suppress_warnings": True
}
