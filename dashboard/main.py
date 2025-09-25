"""
Main module for COVID-19 Belgium Dashboard

This module provides the main entry point and orchestrates the complete
data processing and dashboard creation pipeline.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from config import FILE_PATHS, DASHBOARD_CONFIG
from data_processing import load_and_process_all_data
from visualization import (
    load_and_process_geospatial_data, 
    prepare_dashboard_data,
    create_dashboard_app,
    launch_dashboard
)
from utils import setup_logging, validate_data_quality

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


def run_data_pipeline(force_reload: bool = False) -> str:
    """
    Run the complete data processing pipeline.
    
    Args:
        force_reload: If True, reprocess data even if intermediate file exists
        
    Returns:
        str: Path to the processed data file
    """
    logger.info("🚀 Starting COVID-19 Belgium data processing pipeline...")
    
    # Check if intermediate data already exists
    if FILE_PATHS["intermediate_data"].exists() and not force_reload:
        logger.info(f"✅ Using existing processed data: {FILE_PATHS['intermediate_data']}")
        return str(FILE_PATHS["intermediate_data"])
    
    try:
        # Run complete processing pipeline
        processed_data = load_and_process_all_data()
        logger.info("✅ Data processing pipeline completed successfully!")
        return str(FILE_PATHS["intermediate_data"])
        
    except Exception as e:
        logger.error(f"❌ Data processing pipeline failed: {e}")
        raise


def create_and_launch_dashboard(data_file: Optional[str] = None,
                               time_filter: Optional[Tuple[datetime, datetime]] = None,
                               launch: bool = True) -> object:
    """
    Create and optionally launch the interactive dashboard.
    
    Args:
        data_file: Path to processed data file (if None, uses default)
        time_filter: Optional tuple of (start_date, end_date) to filter data
        launch: Whether to launch the dashboard server
        
    Returns:
        Dash app object
    """
    logger.info("🎛️ Creating interactive dashboard...")
    
    try:
        # Load processed data
        if data_file is None:
            data_file = str(FILE_PATHS["intermediate_data"])
        
        import pandas as pd
        covid_data = pd.read_csv(data_file)
        logger.info(f"✅ Loaded {len(covid_data):,} records from {data_file}")
        
        # Validate data quality
        required_columns = ['NIS5', 'CASES', 'SI', 'vacc_pct', 'POPULATION', 'year', 'week']
        validation_results = validate_data_quality(covid_data, required_columns)
        
        if not validation_results['is_valid']:
            logger.warning(f"⚠️ Data validation issues: {validation_results['missing_columns']}")
        
        # Convert date information
        if 'date' not in covid_data.columns and 'year' in covid_data.columns and 'week' in covid_data.columns:
            from visualization import iso_to_date
            covid_data['date'] = covid_data.apply(
                lambda row: iso_to_date(row['year'], row['week']), axis=1
            )
        
        # Load geospatial data
        geo_data = load_and_process_geospatial_data(covid_data)
        
        # Prepare dashboard data
        prepared_data = prepare_dashboard_data(geo_data, time_filter)
        
        # Create dashboard app
        app = create_dashboard_app(prepared_data)
        
        if launch:
            launch_dashboard(app)
        
        return app
        
    except Exception as e:
        logger.error(f"❌ Dashboard creation failed: {e}")
        raise


def main(force_reload: bool = False,
         time_filter: Optional[Tuple[str, str]] = None,
         launch_dashboard_flag: bool = True):
    """
    Main execution function for the COVID-19 Belgium Dashboard.
    
    Args:
        force_reload: Force reprocessing of data
        time_filter: Optional tuple of (start_date, end_date) as strings
        launch_dashboard_flag: Whether to launch the dashboard
    """
    logger.info("=" * 60)
    logger.info("🇧🇪 COVID-19 Belgium Dashboard")
    logger.info("=" * 60)
    
    try:
        # Step 1: Process data
        logger.info("📊 Step 1: Data Processing")
        data_file = run_data_pipeline(force_reload=force_reload)
        
        # Step 2: Prepare time filter
        parsed_time_filter = None
        if time_filter:
            try:
                start_date = datetime.strptime(time_filter[0], '%Y-%m-%d')
                end_date = datetime.strptime(time_filter[1], '%Y-%m-%d')
                parsed_time_filter = (start_date, end_date)
                logger.info(f"⏰ Time filter: {start_date.date()} to {end_date.date()}")
            except ValueError as e:
                logger.warning(f"⚠️ Invalid time filter format: {e}. Expected YYYY-MM-DD")
        
        # Step 3: Create and launch dashboard
        logger.info("🎛️ Step 2: Dashboard Creation")
        app = create_and_launch_dashboard(
            data_file=data_file,
            time_filter=parsed_time_filter,
            launch=launch_dashboard_flag
        )
        
        if not launch_dashboard_flag:
            logger.info("✅ Dashboard created but not launched. Return the app object to launch manually.")
            return app
        
    except KeyboardInterrupt:
        logger.info("👋 Dashboard stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")
        raise


def quick_start_demo():
    """
    Quick start demonstration with early filtering for fast loading.
    This mimics the original notebook's approach of filtering early.
    """
    logger.info("🚀 Quick Start Demo - COVID-19 Belgium Dashboard")
    logger.info("Using October 2020 data for faster demonstration...")
    
    try:
        # Create a quick demo dataset with early filtering (like original notebook)
        demo_data_file = _create_quick_demo_dataset()
        
        # Create dashboard with the pre-filtered data
        app = create_and_launch_dashboard(
            data_file=demo_data_file,
            time_filter=None,  # No additional filtering needed
            launch=True
        )
        
        return app
        
    except Exception as e:
        logger.error(f"❌ Quick demo failed: {e}")
        logger.info("🔄 Falling back to regular time-filtered approach...")
        
        # Fallback to original approach if needed
        demo_time_filter = ('2020-10-01', '2020-10-31')
        main(
            force_reload=False,
            time_filter=demo_time_filter,
            launch_dashboard_flag=True
        )


def _create_quick_demo_dataset() -> str:
    """
    Create a quick demo dataset with early filtering (October 2020 only).
    Returns path to the demo dataset file.
    """
    from datetime import datetime
    import pandas as pd
    from data_processing import (
        download_and_load_covid_cases, download_and_load_vaccination_data,
        load_population_data, load_oxford_stringency_data,
        create_week_to_month_mapping, process_oxford_stringency_data
    )
    from visualization import iso_to_date
    
    demo_file = FILE_PATHS["intermediate_data"].parent / "demo_data_october_2020.csv"
    
    # Use cached demo data if available and recent
    if demo_file.exists():
        logger.info(f"✅ Using cached demo data: {demo_file}")
        return str(demo_file)
    
    logger.info("🚀 Creating quick demo dataset (October 2020 only)...")
    
    # Step 1: Load raw data
    covid_cases = download_and_load_covid_cases()
    vacc_data = download_and_load_vaccination_data()
    population = load_population_data()
    oxford_raw = load_oxford_stringency_data()
    
    # Step 2: EARLY FILTERING - Filter to October 2020 weeks only (like original)
    week_to_month_link = create_week_to_month_mapping()
    covid_cases = covid_cases.merge(week_to_month_link, on=["year", "week"], how='left')
    
    # Filter COVID data to October 2020 only (weeks 41-44)
    covid_cases = covid_cases[
        (covid_cases['year'] == 2020) & 
        (covid_cases['week'].isin([41, 42, 43, 44]))
    ].copy()
    
    logger.info(f"📊 Filtered COVID data to {len(covid_cases):,} records (October 2020 only)")
    
    # Create weekly aggregation (much smaller now!)
    covid_cases_weekly = covid_cases.groupby([
        "NIS5", "year", "week", "TX_DESCR_NL", "TX_ADM_DSTR_DESCR_NL", 
        "PROVINCE", "REGION"
    ])[["CASES"]].sum().reset_index()
    
    # Step 3: Process other data for the same period
    # Filter vaccination data to October 2020
    vacc_data = vacc_data[
        (vacc_data['year'] == 2020) & 
        (vacc_data['week'].isin([41, 42, 43, 44]))
    ].copy()
    
    # Process Oxford data for October 2020 only
    oxford_weekly = process_oxford_stringency_data(oxford_raw)
    oxford_weekly = oxford_weekly[
        (oxford_weekly['year'] == 2020) & 
        (oxford_weekly['week'].isin([41, 42, 43, 44]))
    ].copy()
    
    # Step 4: Create balanced panel (small!)
    municipalities = covid_cases_weekly[[
        'NIS5', 'TX_DESCR_NL', 'TX_ADM_DSTR_DESCR_NL', 'PROVINCE', 'REGION'
    ]].drop_duplicates()
    
    # Only weeks 41-44 of 2020
    weeks_data = pd.DataFrame({
        'year': [2020] * 4,
        'week': [41, 42, 43, 44]
    })
    
    # Create complete panel (should be 581 municipalities × 4 weeks = 2,324 records)
    complete_panel = municipalities.merge(weeks_data, how='cross')
    
    # Merge all datasets
    demo_data = complete_panel.merge(
        covid_cases_weekly, 
        on=['NIS5', 'year', 'week', 'TX_DESCR_NL', 'TX_ADM_DSTR_DESCR_NL', 'PROVINCE', 'REGION'], 
        how='left'
    )
    
    demo_data = demo_data.merge(
        vacc_data[['NIS5', 'year', 'week', 'cvacc']], 
        on=['NIS5', 'year', 'week'], 
        how='left'
    )
    
    demo_data = demo_data.merge(
        population, 
        how="left", left_on=['NIS5'], right_on=['CD_REFNIS']
    )
    
    demo_data = demo_data.merge(
        oxford_weekly, 
        how="left", 
        left_on=['year', 'week', 'PROVINCE'], 
        right_on=['year', 'week', 'Province']
    ).drop(columns=['Province', 'Region'], errors='ignore')
    
    # Clean up duplicate columns from merges
    columns_to_drop = [col for col in demo_data.columns if col.endswith('_y')]
    if columns_to_drop:
        demo_data = demo_data.drop(columns=columns_to_drop)
    
    demo_data = demo_data.merge(week_to_month_link, on=["year", "week"], how='left')
    
    # Fill missing values
    demo_data['CASES'] = demo_data['CASES'].fillna(0)
    demo_data['cvacc'] = demo_data['cvacc'].fillna(0)
    demo_data['vacc_pct'] = (demo_data['cvacc'] / demo_data['POPULATION'] * 100).fillna(0)
    
    # Add date column
    demo_data['date'] = demo_data.apply(lambda row: iso_to_date(row['year'], row['week']), axis=1)
    
    # Save demo data
    demo_data.to_csv(demo_file, index=False)
    
    logger.info(f"✅ Quick demo dataset created: {len(demo_data):,} records saved to {demo_file}")
    logger.info(f"📅 Date range: {demo_data['date'].min()} to {demo_data['date'].max()}")
    
    return str(demo_file)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="COVID-19 Belgium Dashboard - Interactive Analysis Tool"
    )
    parser.add_argument(
        "--force-reload", 
        action="store_true",
        help="Force reprocessing of data even if cached version exists"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for time filter (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--end-date", 
        type=str,
        help="End date for time filter (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run quick start demo with limited data"
    )
    parser.add_argument(
        "--no-launch",
        action="store_true", 
        help="Create dashboard but don't launch server"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        quick_start_demo()
    else:
        time_filter = None
        if args.start_date and args.end_date:
            time_filter = (args.start_date, args.end_date)
        elif args.start_date or args.end_date:
            logger.warning("⚠️ Both start-date and end-date must be provided for time filtering")
        
        main(
            force_reload=args.force_reload,
            time_filter=time_filter,
            launch_dashboard_flag=not args.no_launch
        )
