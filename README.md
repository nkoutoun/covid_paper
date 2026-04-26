# Belgium COVID-19 Interactive Dashboard

[![Live Demo](https://img.shields.io/badge/demo-online-brightgreen)](https://covid-belgium-dashboard.onrender.com)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/dash-2.0%2B-119DFF)](https://dash.plotly.com/)
[![DOI](https://img.shields.io/badge/DOI-10.1016%2Fj.jmacro.2025.103677-orange)](https://doi.org/10.1016/j.jmacro.2025.103677)

A web dashboard for exploring COVID-19 incidence, vaccination, and government-response data across the 581 Belgian municipalities (2019–2022).

**Live demo:** [covid-belgium-dashboard.onrender.com](https://covid-belgium-dashboard.onrender.com)

---

## Overview

The dashboard accompanies the research paper below and provides an interactive view of municipality-level pandemic indicators on a choropleth map with a temporal slider:

> De Schryder, S., Koutounidis, N., Schoors, K., & Weytjens, J. (2025).
> *Assessing the Heterogeneous Impact of COVID-19 on Consumption Using Bank Transactions.*
> **Journal of Macroeconomics** 84:103677. [doi:10.1016/j.jmacro.2025.103677](https://doi.org/10.1016/j.jmacro.2025.103677)

The double-demeaning estimator developed in the paper is published as a separate Python package: [`ddinteract`](https://pypi.org/project/ddinteract/).

## Features

- Choropleth map of Belgian municipalities with real administrative boundaries
- Time slider covering 2019–2022 with adaptive marks
- Switchable variables: COVID-19 cases, stringency index, vaccination rates, population
- Live summary statistics (totals, means, maxima) reactive to the current selection
- Pre-cached GeoJSON and simplified geometries for sub-second interactions

## Installation

Requires Python 3.9 or newer.

```bash
git clone https://github.com/<user>/covid_paper.git
cd covid_paper
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

The dashboard is then served at [http://localhost:8050](http://localhost:8050).

## Project Structure

```
.
├── app.py                # Dash application entry point
├── config.py             # Application configuration
├── data_processing.py    # Shapefile and dataset utilities
├── data/                 # COVID-19 dataset (~91K records)
├── data_public/
│   └── municipalities/   # Pre-aggregated Belgian boundaries
├── requirements.txt
└── render.yaml           # Render.com deployment config
```

## Data Sources

| Source | Provider | Notes |
| --- | --- | --- |
| COVID-19 cases | Sciensano | Counts <5 per municipality/day are set to 1 for privacy |
| Vaccination | Sciensano | Municipality-level coverage |
| Government response | Oxford COVID-19 Government Response Tracker | Stringency index |
| Geographic boundaries | StatBel | Pre-aggregated from sectors to 581 municipalities |

## Deployment

The repository is configured for one-click deployment to [Render](https://render.com) via [`render.yaml`](render.yaml). Builds run automatically on push; the service is memory-optimized for the free tier.

## Citation

If you use this dashboard or the underlying data processing in your work, please cite:

```bibtex
@article{deschryder2025covid,
  title   = {Assessing the Heterogeneous Impact of COVID-19 on Consumption Using Bank Transactions},
  author  = {De Schryder, Selien and Koutounidis, Nikolaos and Schoors, Koen and Weytjens, Jonas},
  journal = {Journal of Macroeconomics},
  volume  = {84},
  pages   = {103677},
  year    = {2025},
  doi     = {10.1016/j.jmacro.2025.103677}
}
```

## Contact

Maintained by **Nikolaos Koutounidis** (Ghent University). For questions about the data, methodology, or collaboration, please open an issue or get in touch.
