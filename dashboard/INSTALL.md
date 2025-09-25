# Installation Guide - COVID-19 Belgium Dashboard

## Quick Installation

### 1. System Requirements
- Python 3.8 or higher
- 4GB RAM (8GB recommended)
- Internet connection for data downloads

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Prepare Data Files
Place the following files in the `dashboard/data/` folder:
- `population_by_NIS.xlsx` - Population data by municipality
- `si_be_muni_daily.xlsx` - Oxford Stringency Index data

### 4. Run Quick Demo
```python
from dashboard import quick_start_demo
quick_start_demo()
```

## Detailed Setup

### Python Environment Setup

#### Option 1: Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv covid_dashboard_env

# Activate (Windows)
covid_dashboard_env\Scripts\activate

# Activate (Linux/Mac)
source covid_dashboard_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Option 2: Conda Environment
```bash
# Create conda environment
conda create -n covid_dashboard python=3.9

# Activate environment
conda activate covid_dashboard

# Install dependencies
pip install -r requirements.txt
```

### Data Preparation

#### Required Local Files
1. **Population Data**: `population_by_NIS.xlsx`
   - Should contain municipality population by NIS code
   - Columns: `CD_REFNIS`, `TX_DESCR_NL`, `POPULATION`

2. **Oxford Data**: `si_be_muni_daily.xlsx`
   - Oxford COVID-19 Government Response Tracker data for Belgium
   - Should have sheet named 'raw_data'

#### Optional Geospatial Data
- Belgian municipality shapefile: `data_public/shapefiles/sh_statbel_statistical_sectors_20190101.shp`
- Download from StatBel (Belgian Statistical Office)
- URL: https://statbel.fgov.be/en/open-data/statistical-sectors-2019
- **Important**: Place the complete shapefile set (`.shp`, `.shx`, `.dbf`, `.prj`) in the `shapefiles/` subfolder

### Verification

Test your installation:
```python
# Test imports
from dashboard import setup_logging, VARIABLE_OPTIONS
from dashboard.config import FILE_PATHS

# Check configuration
print("Available variables:", [opt['label'] for opt in VARIABLE_OPTIONS])
print("Data paths configured:", dict(FILE_PATHS))

# Test quick demo
from dashboard import quick_start_demo
# quick_start_demo()  # Uncomment to run
```

## Troubleshooting

### Common Installation Issues

#### Import Errors
```python
# If you get "ModuleNotFoundError: No module named 'dashboard'"
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath('.')))
```

#### Geospatial Dependencies
If geopandas installation fails:
```bash
# On Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev

# On Windows, use conda
conda install geopandas

# On Mac with Homebrew
brew install gdal
```

#### Plotly/Dash Issues
```bash
# If dashboard doesn't display properly
pip install --upgrade plotly dash
```

### Performance Optimization

#### For Large Datasets
- Use time filtering: `main(time_filter=('2020-10-01', '2020-10-31'))`
- Start with demo: `quick_start_demo()`
- Increase system memory if possible

#### For Slow Startup
- Pre-process data: `run_data_pipeline()` once
- Use cached intermediate data
- Filter to specific time periods

## Development Setup

### Additional Development Tools
```bash
pip install jupyter notebook ipython black flake8 mypy
```

### Jupyter Integration
```bash
# Register the environment as a kernel
python -m ipykernel install --user --name covid_dashboard --display-name "COVID Dashboard"

# Start Jupyter
jupyter notebook dashboard_streamlined.ipynb
```

### Code Quality Tools
```bash
# Format code
black dashboard/

# Check style
flake8 dashboard/

# Type checking
mypy dashboard/
```

## Next Steps

After successful installation:

1. **Run Quick Demo**: `quick_start_demo()` to verify everything works
2. **Explore Notebook**: Open `dashboard_streamlined.ipynb` for guided examples
3. **Read Documentation**: Review `README.md` for detailed usage information
4. **Customize Configuration**: Modify `config.py` for your specific needs

## Support

If you encounter issues:
1. Check this troubleshooting section
2. Verify all data files are present and correctly formatted
3. Ensure all dependencies are properly installed
4. Test with the quick demo first
