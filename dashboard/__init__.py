"""
COVID-19 Belgium Dashboard Package

An interactive dashboard for analyzing COVID-19 data across Belgian municipalities,
featuring temporal analysis, geospatial visualization, and government response tracking.

Usage:
    from dashboard.main import main, quick_start_demo
    
    # Run the full dashboard
    main()
    
    # Run a quick demo
    quick_start_demo()
    
    # Run with custom time filtering
    main(time_filter=('2020-10-01', '2020-12-31'))

Modules:
    - config: Configuration settings and constants
    - data_processing: Data loading and processing functions
    - visualization: Dashboard and mapping functions
    - utils: Utility functions and helpers
    - main: Main execution and orchestration
"""

from main import main, quick_start_demo, run_data_pipeline, create_and_launch_dashboard
from config import VARIABLE_OPTIONS, DASHBOARD_CONFIG
from utils import setup_logging

__version__ = "1.0.0"
__author__ = "Research Team"
__description__ = "Interactive COVID-19 Dashboard for Belgian Municipalities"

# Default imports for easy access
__all__ = [
    'main',
    'quick_start_demo', 
    'run_data_pipeline',
    'create_and_launch_dashboard',
    'setup_logging',
    'VARIABLE_OPTIONS',
    'DASHBOARD_CONFIG'
]
