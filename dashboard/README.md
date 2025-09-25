# COVID-19 Belgium Dashboard

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An interactive dashboard for analyzing COVID-19 data across Belgian municipalities with temporal analysis, geospatial visualization, and government response tracking.

## Features

- **📊 Interactive Maps**: Municipality-level COVID-19 visualization  
- **🦠 Multiple Variables**: Cases, vaccination rates, stringency index, population
- **📅 Time Controls**: Week-by-week analysis with temporal slider
- **⚡ Performance Optimized**: Cached processing for responsive interactions

## Architecture

```
dashboard/
├── main.py              # Main execution and orchestration  
├── config.py            # Configuration settings
├── data_processing.py   # Data loading and processing
├── visualization.py     # Dashboard and mapping
├── utils.py             # Helper functions
├── data/                # Local data files
└── data_public/         # Downloaded public data
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare Data
Place these files in `dashboard/data/`:
- `population_by_NIS.xlsx` - Municipality population data
- `si_be_muni_daily.xlsx` - Oxford Stringency Index data

### 3. Run Dashboard
```python
# Quick demo (recommended first run)
from dashboard import quick_start_demo
quick_start_demo()

# Full dashboard
from dashboard import main
main()

# Command line
python -m dashboard.main --demo
```

## Data Sources

**Automatically Downloaded:**
- COVID-19 cases: Sciensano (Belgian Institute for Health)
- Vaccination data: Sciensano

**Required Local Files:**
- Population data by municipality
- Oxford COVID-19 Government Response Tracker data

## Usage Examples

```python
# Basic usage
from dashboard import main
main()

# Time filtering
main(time_filter=('2020-10-01', '2020-12-31'))

# Force data refresh
main(force_reload=True)
```

## Configuration

Modify `config.py` for custom settings:

```python
DASHBOARD_CONFIG = {
    "host": "127.0.0.1",
    "port": 8050,
    "debug": True,
    "map_center": {"lat": 50.8503, "lon": 4.3517}
}
```

## Requirements

- Python 3.8+
- 4GB RAM (8GB recommended)
- Internet connection for data downloads
- Modern web browser

## Common Issues

**Missing data files**: Ensure required files are in `data/` folder  
**Dashboard won't start**: Check if port 8050 is available  
**Slow performance**: Use time filtering or run quick demo first  
**Import errors**: Ensure dashboard is in Python path

## License

MIT License

## Citation

```bibtex
@software{covid_belgium_dashboard,
  title={COVID-19 Belgium Dashboard: Interactive Municipality Analysis},
  author={[Author Name]},
  year={2024},
  url={[Repository URL]}
}
```

---

*Research-grade dashboard for COVID-19 analysis in Belgium with modular architecture for academic collaboration.*
