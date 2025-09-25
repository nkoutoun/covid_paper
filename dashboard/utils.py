"""
Utility functions for COVID-19 Belgium Dashboard

This module contains helper functions and utilities used across
the dashboard application.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Union, Optional, List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_data_quality(data: pd.DataFrame, required_columns: List[str]) -> Dict[str, Union[bool, List[str]]]:
    """
    Validate data quality and check for required columns.
    
    Args:
        data: DataFrame to validate
        required_columns: List of column names that must be present
        
    Returns:
        Dict with validation results
    """
    results = {
        'is_valid': True,
        'missing_columns': [],
        'empty_columns': [],
        'data_shape': data.shape,
        'missing_values': {}
    }
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        results['is_valid'] = False
        results['missing_columns'] = missing_columns
    
    # Check for empty columns
    empty_columns = [col for col in data.columns if data[col].isna().all()]
    if empty_columns:
        results['empty_columns'] = empty_columns
    
    # Check missing values in required columns
    for col in required_columns:
        if col in data.columns:
            missing_count = data[col].isna().sum()
            if missing_count > 0:
                results['missing_values'][col] = missing_count
    
    return results


def clean_numeric_column(series: pd.Series, 
                        replacement_map: Optional[Dict[str, Union[int, float]]] = None) -> pd.Series:
    """
    Clean and convert a series to numeric, handling common data issues.
    
    Args:
        series: Pandas series to clean
        replacement_map: Dictionary mapping string values to numeric replacements
        
    Returns:
        pd.Series: Cleaned numeric series
    """
    if replacement_map is None:
        replacement_map = {'<5': 1, '<10': 1, 'NA': 0, 'NULL': 0}
    
    # Apply replacements
    cleaned_series = series.copy()
    for old_val, new_val in replacement_map.items():
        cleaned_series = cleaned_series.replace(old_val, new_val)
    
    # Convert to numeric
    cleaned_series = pd.to_numeric(cleaned_series, errors='coerce')
    
    return cleaned_series


def standardize_date_column(data: pd.DataFrame, date_column: str) -> pd.DataFrame:
    """
    Standardize date column and add ISO week/year information.
    
    Args:
        data: DataFrame containing date column
        date_column: Name of the date column
        
    Returns:
        pd.DataFrame: Data with standardized date and time columns
    """
    data_copy = data.copy()
    
    # Convert to datetime
    data_copy[date_column] = pd.to_datetime(data_copy[date_column])
    
    # Add ISO calendar information
    data_copy[['year', 'week', 'day']] = data_copy[date_column].dt.isocalendar()
    
    return data_copy


def calculate_rates_and_percentages(data: pd.DataFrame, 
                                  numerator_col: str, 
                                  denominator_col: str,
                                  rate_name: str,
                                  rate_per: int = 1000) -> pd.DataFrame:
    """
    Calculate rates and percentages from count data.
    
    Args:
        data: DataFrame with count data
        numerator_col: Column name for numerator
        denominator_col: Column name for denominator  
        rate_name: Name for the new rate column
        rate_per: Rate per X population (default 1000)
        
    Returns:
        pd.DataFrame: Data with calculated rate column
    """
    data_copy = data.copy()
    
    # Calculate rate, handling division by zero
    data_copy[rate_name] = np.where(
        data_copy[denominator_col] > 0,
        (data_copy[numerator_col] / data_copy[denominator_col]) * rate_per,
        0
    )
    
    return data_copy


def filter_by_date_range(data: pd.DataFrame, 
                        date_column: str,
                        start_date: Optional[Union[str, datetime]] = None,
                        end_date: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
    """
    Filter DataFrame by date range.
    
    Args:
        data: DataFrame with date column
        date_column: Name of date column
        start_date: Start date for filtering
        end_date: End date for filtering
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    data_copy = data.copy()
    
    # Ensure date column is datetime
    data_copy[date_column] = pd.to_datetime(data_copy[date_column])
    
    if start_date:
        start_date = pd.to_datetime(start_date)
        data_copy = data_copy[data_copy[date_column] >= start_date]
    
    if end_date:
        end_date = pd.to_datetime(end_date)
        data_copy = data_copy[data_copy[date_column] <= end_date]
    
    logger.info(f"Filtered data from {len(data)} to {len(data_copy)} records")
    return data_copy


def aggregate_to_time_period(data: pd.DataFrame,
                           groupby_cols: List[str],
                           agg_cols: List[str],
                           agg_func: str = 'sum') -> pd.DataFrame:
    """
    Aggregate data to specified time period.
    
    Args:
        data: DataFrame to aggregate
        groupby_cols: Columns to group by
        agg_cols: Columns to aggregate
        agg_func: Aggregation function (sum, mean, etc.)
        
    Returns:
        pd.DataFrame: Aggregated data
    """
    agg_dict = {col: agg_func for col in agg_cols}
    
    aggregated = data.groupby(groupby_cols).agg(agg_dict).reset_index()
    
    logger.info(f"Aggregated data from {len(data)} to {len(aggregated)} records")
    return aggregated


def create_balanced_time_series(data: pd.DataFrame,
                              entity_col: str,
                              time_cols: List[str],
                              time_ranges: Dict[str, List]) -> pd.DataFrame:
    """
    Create a balanced panel with all entity-time combinations.
    
    Args:
        data: Input DataFrame
        entity_col: Column identifying entities (e.g., municipalities)
        time_cols: List of time columns (e.g., ['year', 'week'])
        time_ranges: Dict mapping time columns to their possible values
        
    Returns:
        pd.DataFrame: Balanced panel
    """
    # Get unique entities
    entities = data[entity_col].unique()
    
    # Create all time combinations
    import itertools
    time_combinations = list(itertools.product(*time_ranges.values()))
    time_df = pd.DataFrame(time_combinations, columns=time_cols)
    
    # Create entity-time combinations
    entity_df = pd.DataFrame({entity_col: entities})
    balanced_panel = entity_df.merge(time_df, how='cross')
    
    logger.info(f"Created balanced panel with {len(balanced_panel)} entity-time combinations")
    return balanced_panel


def format_large_numbers(number: Union[int, float], precision: int = 1) -> str:
    """
    Format large numbers with appropriate suffixes (K, M, B).
    
    Args:
        number: Number to format
        precision: Decimal precision
        
    Returns:
        str: Formatted number string
    """
    if pd.isna(number):
        return "N/A"
    
    if abs(number) >= 1_000_000_000:
        return f"{number/1_000_000_000:.{precision}f}B"
    elif abs(number) >= 1_000_000:
        return f"{number/1_000_000:.{precision}f}M"
    elif abs(number) >= 1_000:
        return f"{number/1_000:.{precision}f}K"
    else:
        return f"{number:.{precision}f}"


def calculate_summary_statistics(data: pd.DataFrame, 
                               numeric_cols: List[str]) -> pd.DataFrame:
    """
    Calculate summary statistics for numeric columns.
    
    Args:
        data: Input DataFrame
        numeric_cols: List of numeric columns to analyze
        
    Returns:
        pd.DataFrame: Summary statistics
    """
    summary_stats = []
    
    for col in numeric_cols:
        if col in data.columns:
            stats = {
                'variable': col,
                'count': data[col].count(),
                'mean': data[col].mean(),
                'std': data[col].std(),
                'min': data[col].min(),
                'q25': data[col].quantile(0.25),
                'median': data[col].median(),
                'q75': data[col].quantile(0.75),
                'max': data[col].max(),
                'missing': data[col].isna().sum()
            }
            summary_stats.append(stats)
    
    return pd.DataFrame(summary_stats)


def detect_outliers(data: pd.DataFrame, 
                   column: str,
                   method: str = 'iqr',
                   threshold: float = 1.5) -> pd.Series:
    """
    Detect outliers in a numeric column.
    
    Args:
        data: DataFrame containing the data
        column: Column name to analyze
        method: Method for outlier detection ('iqr' or 'zscore')
        threshold: Threshold for outlier detection
        
    Returns:
        pd.Series: Boolean series indicating outliers
    """
    if method == 'iqr':
        q1 = data[column].quantile(0.25)
        q3 = data[column].quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        outliers = (data[column] < lower_bound) | (data[column] > upper_bound)
        
    elif method == 'zscore':
        z_scores = np.abs((data[column] - data[column].mean()) / data[column].std())
        outliers = z_scores > threshold
        
    else:
        raise ValueError("Method must be 'iqr' or 'zscore'")
    
    logger.info(f"Detected {outliers.sum()} outliers in column '{column}' using {method} method")
    return outliers


def create_data_dictionary() -> Dict[str, str]:
    """
    Create a data dictionary describing all variables.
    
    Returns:
        Dict: Data dictionary with variable descriptions
    """
    return {
        'NIS5': 'Belgian municipality identifier (5 digits)',
        'TX_DESCR_NL': 'Municipality name in Dutch',
        'TX_ADM_DSTR_DESCR_NL': 'Administrative district name in Dutch', 
        'PROVINCE': 'Province name',
        'REGION': 'Region name (Flanders, Wallonia, Brussels)',
        'year': 'ISO calendar year',
        'week': 'ISO week number',
        'month': 'Calendar month',
        'date': 'Date (Monday of the ISO week)',
        'CASES': 'Weekly COVID-19 cases',
        'cvacc': 'Cumulative vaccinations',
        'vacc_pct': 'Vaccination percentage of population',
        'POPULATION': 'Municipality population',
        'SI': 'Stringency Index (0-100)',
        'GRI': 'Government Response Index (0-100)',
        'CHI': 'Containment and Health Index (0-100)',
        'ESI': 'Economic Support Index (0-100)',
        'cases_per_1000': 'COVID-19 cases per 1000 population'
    }
