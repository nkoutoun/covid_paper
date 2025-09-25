"""
Utility functions for data validation and preparation in double demeaning analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


def validate_panel_data(data: pd.DataFrame, unit_var: str, time_var: str) -> pd.DataFrame:
    """
    Validate and basic preparation of panel data.
    
    Parameters
    ----------
    data : pd.DataFrame
        Input panel dataset
    unit_var : str
        Name of unit identifier variable
    time_var : str
        Name of time identifier variable
        
    Returns
    -------
    pd.DataFrame
        Validated panel data
        
    Raises
    ------
    ValueError
        If required variables are missing or data structure is invalid
    """
    
    # Check required columns exist
    required_cols = [unit_var, time_var]
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        raise ValueError(f"Required columns missing: {missing_cols}")
    
    # Check for missing values in ID variables
    if data[unit_var].isnull().any():
        raise ValueError(f"Missing values found in unit variable '{unit_var}'")
    if data[time_var].isnull().any():
        raise ValueError(f"Missing values found in time variable '{time_var}'")
    
    # Check minimum panel requirements
    panel_structure = data.groupby(unit_var)[time_var].count()
    units_with_single_obs = (panel_structure == 1).sum()
    
    if units_with_single_obs > 0:
        print(f"⚠️  Warning: {units_with_single_obs} units have only 1 observation")
        print("   Fixed effects models require multiple observations per unit")
    
    # Check for balanced vs unbalanced panel
    unique_periods = panel_structure.unique()
    is_balanced = len(unique_periods) == 1
    
    print(f"📊 Panel Data Summary:")
    print(f"   Total observations: {len(data):,}")
    print(f"   Number of units: {data[unit_var].nunique():,}")
    print(f"   Time periods per unit: {panel_structure.min()}-{panel_structure.max()}")
    print(f"   Panel type: {'Balanced' if is_balanced else 'Unbalanced'}")
    
    return data


def check_within_unit_variation(data: pd.DataFrame, variable: str, 
                               min_variation_threshold: float = 0.05) -> Dict:
    """
    Check within-unit variation for a variable in panel data.
    
    This is crucial for fixed effects models as variables with no within-unit
    variation will be perfectly collinear with the fixed effects.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data with MultiIndex [unit, time] or unit/time columns
    variable : str
        Variable name to check
    min_variation_threshold : float, optional
        Minimum fraction of units that must have variation (default: 0.05)
        
    Returns
    -------
    Dict
        Dictionary with variation statistics
    """
    
    if variable not in data.columns:
        return {'error': f"Variable '{variable}' not found in data"}
    
    # Handle both MultiIndex and regular DataFrame
    if isinstance(data.index, pd.MultiIndex):
        # Data is already indexed by [unit, time]
        grouped = data.groupby(level=0)[variable]
    else:
        # Assume first column is unit identifier
        unit_col = data.columns[0]
        grouped = data.groupby(unit_col)[variable]
    
    # Calculate within-unit statistics
    unit_stats = grouped.agg(['count', 'std', 'min', 'max']).fillna(0)
    
    # Units with variation (standard deviation > 0 and more than 1 observation)
    units_with_variation = ((unit_stats['std'] > 1e-10) & (unit_stats['count'] > 1)).sum()
    total_units = len(unit_stats)
    units_without_variation = total_units - units_with_variation
    
    # Calculate variation metrics
    pct_with_variation = units_with_variation / total_units if total_units > 0 else 0
    meets_threshold = pct_with_variation >= min_variation_threshold
    
    # Overall variation statistics
    overall_std = data[variable].std()
    within_unit_std = unit_stats['std'].mean()
    between_unit_std = grouped.mean().std()
    
    return {
        'variable': variable,
        'total_units': total_units,
        'units_with_variation': units_with_variation,
        'units_without_variation': units_without_variation,
        'pct_with_variation': pct_with_variation,
        'meets_threshold': meets_threshold,
        'threshold_used': min_variation_threshold,
        'overall_std': overall_std,
        'within_unit_std': within_unit_std,
        'between_unit_std': between_unit_std,
        'avg_periods_per_unit': unit_stats['count'].mean()
    }


def prepare_panel_data(data: pd.DataFrame, unit_var: str, time_var: str, 
                      variables: List[str]) -> pd.DataFrame:
    """
    Prepare panel data for analysis including filtering and type conversion.
    
    Parameters
    ----------
    data : pd.DataFrame
        Input panel dataset
    unit_var : str
        Unit identifier variable
    time_var : str
        Time identifier variable  
    variables : List[str]
        List of variables to prepare
        
    Returns
    -------
    pd.DataFrame
        Prepared panel data
    """
    
    # Select relevant columns
    all_vars = [unit_var, time_var] + variables
    available_vars = [var for var in all_vars if var in data.columns]
    
    if len(available_vars) < len(all_vars):
        missing = set(all_vars) - set(available_vars)
        print(f"⚠️  Warning: Variables not found in data: {missing}")
    
    df_prep = data[available_vars].copy()
    
    # Handle missing values
    missing_before = df_prep.isnull().sum().sum()
    if missing_before > 0:
        print(f"📋 Missing Data Handling:")
        print(f"   Total missing values: {missing_before:,}")
        
        # Show missing by variable
        missing_by_var = df_prep.isnull().sum()
        for var, count in missing_by_var[missing_by_var > 0].items():
            pct = 100 * count / len(df_prep)
            print(f"   {var}: {count:,} ({pct:.1f}%)")
        
        # Drop rows with missing values (listwise deletion)
        df_prep = df_prep.dropna()
        missing_after = len(data) - len(df_prep)
        
        print(f"   Observations dropped due to missing data: {missing_after:,}")
        print(f"   Final sample size: {len(df_prep):,}")
    
    # Data type conversion for analysis variables
    numeric_vars = [var for var in variables if var in df_prep.columns]
    
    print(f"📋 Data Type Conversion:")
    for var in numeric_vars:
        original_dtype = df_prep[var].dtype
        
        if original_dtype.name in ['category', 'object']:
            try:
                # Handle categorical variables more carefully
                if original_dtype.name == 'category':
                    if pd.api.types.is_numeric_dtype(df_prep[var].cat.codes):
                        # Check if categories are numeric
                        if df_prep[var].cat.categories.dtype.kind in 'biufc':  # numeric categories
                            df_prep[var] = pd.to_numeric(df_prep[var], errors='coerce')
                        else:
                            df_prep[var] = df_prep[var].cat.codes.astype(float)
                    else:
                        df_prep[var] = pd.to_numeric(df_prep[var], errors='coerce')
                else:
                    # For object type, try direct conversion
                    df_prep[var] = pd.to_numeric(df_prep[var], errors='coerce')
                
                new_dtype = df_prep[var].dtype
                
                # Only print if there was an actual conversion
                if original_dtype != new_dtype:
                    print(f"   {var}: {original_dtype} → {new_dtype}")
                
                # Check for conversion issues
                new_missing = df_prep[var].isnull().sum()
                if new_missing > 0:
                    print(f"     ⚠️  Warning: {new_missing} values became NaN during conversion")
                    
            except Exception as e:
                print(f"   ⚠️  Warning: Could not convert {var} to numeric: {e}")
        elif not pd.api.types.is_numeric_dtype(df_prep[var]):
            # Try to convert non-numeric types
            try:
                df_prep[var] = pd.to_numeric(df_prep[var], errors='coerce')
                new_dtype = df_prep[var].dtype
                if original_dtype != new_dtype:
                    print(f"   {var}: {original_dtype} → {new_dtype}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not convert {var} to numeric: {e}")
    
    # Final cleanup of any new missing values
    if df_prep.isnull().sum().sum() > 0:
        df_prep = df_prep.dropna()
        print(f"   Final sample after type conversion: {len(df_prep):,}")
    
    return df_prep


def filter_units_by_time_periods(data: pd.DataFrame, unit_var: str, 
                                min_periods: int = 3) -> pd.DataFrame:
    """
    Filter panel data to keep only units with sufficient time periods.
    
    Double demeaning requires T > 2 for proper identification.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel dataset
    unit_var : str
        Unit identifier variable
    min_periods : int, optional
        Minimum number of time periods required (default: 3)
        
    Returns
    -------
    pd.DataFrame
        Filtered dataset
    """
    
    # Count periods per unit
    unit_periods = data.groupby(unit_var).size()
    
    # Identify units to keep
    units_to_keep = unit_periods[unit_periods >= min_periods].index
    units_dropped = len(unit_periods) - len(units_to_keep)
    obs_dropped = data[~data[unit_var].isin(units_to_keep)].shape[0]
    
    print(f"📋 Filtering Units by Time Periods:")
    print(f"   Minimum periods required: {min_periods}")
    print(f"   Units dropped: {units_dropped:,}")
    print(f"   Observations dropped: {obs_dropped:,}")
    
    # Filter data
    filtered_data = data[data[unit_var].isin(units_to_keep)].copy()
    
    print(f"   Final sample: {len(filtered_data):,} observations, {filtered_data[unit_var].nunique():,} units")
    
    return filtered_data


def summarize_panel_structure(data: pd.DataFrame, unit_var: str, time_var: str) -> Dict:
    """
    Provide comprehensive summary of panel data structure.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel dataset
    unit_var : str
        Unit identifier variable
    time_var : str
        Time identifier variable
        
    Returns
    -------
    Dict
        Dictionary with panel structure summary
    """
    
    # Basic counts
    n_obs = len(data)
    n_units = data[unit_var].nunique()
    n_periods = data[time_var].nunique()
    
    # Time periods per unit
    periods_per_unit = data.groupby(unit_var)[time_var].nunique()
    min_t = periods_per_unit.min()
    max_t = periods_per_unit.max()
    mean_t = periods_per_unit.mean()
    
    # Unit distribution across time periods
    units_by_periods = periods_per_unit.value_counts().sort_index()
    
    # Balance check
    is_balanced = len(periods_per_unit.unique()) == 1
    
    # Units with insufficient periods for double demeaning
    units_insufficient = (periods_per_unit <= 2).sum()
    
    # Missing data check
    missing_data = data.isnull().sum()
    total_missing = missing_data.sum()
    
    print(f"📊 COMPREHENSIVE PANEL DATA SUMMARY")
    print(f"=" * 50)
    print(f"📋 Basic Structure:")
    print(f"   Total observations: {n_obs:,}")
    print(f"   Number of units: {n_units:,}")
    print(f"   Number of time periods: {n_periods}")
    print(f"   Average observations per unit: {n_obs/n_units:.1f}")
    
    print(f"\n⏰ Time Structure:")
    print(f"   Min periods per unit: {min_t}")
    print(f"   Max periods per unit: {max_t}")
    print(f"   Mean periods per unit: {mean_t:.1f}")
    
    print(f"\n📊 Unit Distribution by Time Periods:")
    for periods, count in units_by_periods.items():
        pct = 100 * count / n_units
        print(f"   {periods} periods: {count:,} units ({pct:.1f}%)")
    
    # Balance check
    print(f"\n⚖️  Panel Balance:")
    print(f"   Balanced panel: {'Yes' if is_balanced else 'No'}")
    
    if not is_balanced:
        print(f"   Most common panel length: {periods_per_unit.mode().iloc[0]} periods")
        print(f"   Unbalanced panels are fine for this analysis")
    
    # Missing data check
    print(f"\n❓ Missing Data:")
    print(f"   Total missing values: {total_missing:,}")
    if total_missing > 0:
        print(f"   Variables with missing data:")
        for var, count in missing_data[missing_data > 0].items():
            pct = 100 * count / n_obs
            print(f"      {var}: {count:,} ({pct:.1f}%)")
    else:
        print(f"   ✅ No missing data detected")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if units_insufficient > 0:
        pct_insufficient = 100 * units_insufficient / n_units
        print(f"   🔄 Consider filtering units with ≤ 2 periods ({units_insufficient:,} units, {pct_insufficient:.1f}%)")
        print(f"      Code: df_filtered = df.groupby('{unit_var}').filter(lambda x: len(x) > 2)")
    
    if total_missing > 0:
        print(f"   🧹 Handle missing data before analysis")
        print(f"      Options: listwise deletion, imputation, or missingness modeling")
    
    if not is_balanced:
        print(f"   📊 Unbalanced panel detected - ensure this is appropriate for your research design")
    
    return {
        'n_observations': n_obs,
        'n_units': n_units,
        'n_periods': n_periods,
        'min_periods': min_t,
        'max_periods': max_t,
        'mean_periods': mean_t,
        'units_insufficient': units_insufficient,
        'is_balanced': is_balanced,
        'total_missing': total_missing,
        'meets_requirements': units_insufficient == 0 and total_missing == 0
    }
