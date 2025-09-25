"""
Core functionality for double demeaning analysis in fixed effects models.

This module contains the main classes and functions for implementing the 
double demeaning technique from Giesselmann & Schmidt-Catran (2022).
"""

import pandas as pd
import numpy as np
from linearmodels import PanelOLS
from scipy import stats
from typing import Dict, List, Optional, Tuple, Union
import warnings

from .utils import validate_panel_data, check_within_unit_variation


class DoubleDemeanAnalysis:
    """
    Main class for performing double demeaning analysis on panel data.
    
    This class implements the methodology from:
    Giesselmann, M., & Schmidt-Catran, A. W. (2022). Interactions in Fixed Effects 
    Regression Models. Sociological Methods & Research, 51(3), 1100-1127.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel dataset with unit and time identifiers
    unit_var : str
        Name of unit identifier variable
    time_var : str  
        Name of time identifier variable
    y_var : str
        Name of dependent variable
    x_var : str
        First interacting variable
    z_var : str
        Second interacting variable
    w_vars : List[str], optional
        List of control variable names (default: None)
    """
    
    def __init__(self, data: pd.DataFrame, unit_var: str, time_var: str, 
                 y_var: str, x_var: str, z_var: str, w_vars: Optional[List[str]] = None):
        
        self.unit_var = unit_var
        self.time_var = time_var
        self.y_var = y_var
        self.x_var = x_var
        self.z_var = z_var
        self.w_vars = w_vars or []
        
        # Validate and prepare data
        self.data = validate_panel_data(data, unit_var, time_var)
        self._prepare_data()
        
        # Results storage
        self.results = {}
        
    def _prepare_data(self):
        """Prepare data for analysis including type conversion and indexing."""
        
        # Handle data types (convert categorical to numeric)
        analysis_vars = [self.y_var, self.x_var, self.z_var] + self.w_vars
        for var in analysis_vars:
            if var in self.data.columns:
                if self.data[var].dtype.name in ['category', 'object']:
                    try:
                        # For categorical variables, try to get the codes if they're numeric
                        if self.data[var].dtype.name == 'category':
                            if pd.api.types.is_numeric_dtype(self.data[var].cat.codes):
                                # Convert categorical to numeric using the underlying codes if appropriate
                                if self.data[var].cat.categories.dtype.kind in 'biufc':  # numeric categories
                                    self.data[var] = pd.to_numeric(self.data[var], errors='coerce')
                                else:
                                    self.data[var] = self.data[var].cat.codes.astype(float)
                            else:
                                self.data[var] = pd.to_numeric(self.data[var], errors='coerce')
                        else:
                            # For object type, try direct conversion
                            self.data[var] = pd.to_numeric(self.data[var], errors='coerce')
                        
                        # Check for successful conversion
                        if not pd.api.types.is_numeric_dtype(self.data[var]):
                            print(f"⚠️  Warning: Could not convert {var} to numeric")
                        
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  Warning: Could not convert {var} to numeric: {e}")
        
        # Set panel structure
        if not isinstance(self.data.index, pd.MultiIndex):
            self.data = self.data.set_index([self.unit_var, self.time_var])
            
        print(f"✅ Data prepared: {len(self.data)} observations, {self.data.index.get_level_values(0).nunique()} units")
    
    def run_analysis(self, center_variables: bool = True, run_hausman: bool = True, 
                    verbose: bool = True) -> Dict:
        """
        Run complete double demeaning analysis.
        
        Parameters
        ----------
        center_variables : bool, optional
            Whether to apply grand mean centering (default: True)
        run_hausman : bool, optional
            Whether to run Hausman test (default: True) 
        verbose : bool, optional
            Whether to print detailed output (default: True)
            
        Returns
        -------
        Dict
            Dictionary containing analysis results
        """
        
        if verbose:
            self._print_header()
        
        # Step 1: Data preparation checks
        if verbose:
            print("\n📋 Step 1: Data Preparation")
            self._print_data_info()
        
        # Step 2: Grand mean centering
        df_work = self.data.copy()
        if center_variables:
            if verbose:
                print("\n📋 Step 2: Grand Mean Centering")
            df_work = self._apply_grand_mean_centering(df_work, verbose)
        elif verbose:
            print("\n📋 Step 2: Skipping grand mean centering")
        
        # Step 3: Create double demeaned interaction
        if verbose:
            print("\n📋 Step 3: Double Demeaning Implementation")
        df_dd = create_double_demeaned_interaction(
            df_work, self.x_var, self.z_var, self.unit_var, verbose
        )
        
        # Step 4: Model estimation and comparison  
        if verbose:
            print("\n📋 Step 4: Model Estimation and Comparison")
        standard_results, dd_results, comparison_df = estimate_fe_models(
            df_dd, self.y_var, self.x_var, self.z_var, self.w_vars, verbose
        )
        
        # Step 5: Hausman test
        hausman_results = None
        if run_hausman:
            if verbose:
                print("\n📋 Step 5: Hausman Test for Systematic Differences")
            hausman_results = perform_hausman_test(
                standard_results, dd_results, self.x_var, self.z_var, verbose
            )
        
        # Store and return results
        self.results = {
            'standard_results': standard_results,
            'dd_results': dd_results, 
            'comparison_df': comparison_df,
            'hausman_test': hausman_results,
            'processed_data': df_dd
        }
        
        if verbose:
            print("\n✅ ANALYSIS COMPLETE!")
            print("="*80)
        
        return self.results
    
    def _print_header(self):
        """Print analysis header."""
        print("🚀 STARTING DOUBLE DEMEANING ANALYSIS")
        print("="*80)
        print(f"Dataset: {len(self.data)} observations, {len(self.data.columns)} variables")
        print(f"Panel structure: {self.unit_var} (units) × {self.time_var} (time)")
        print(f"Analysis: {self.y_var} ~ {self.x_var} × {self.z_var} + controls")
        print("="*80)
    
    def _print_data_info(self):
        """Print data preparation information."""
        panel_info = self.data.groupby(level=0).size()
        units_insufficient = (panel_info <= 2).sum()
        
        print(f"   Panel info: {panel_info.nunique()} units, {panel_info.min()}-{panel_info.max()} periods per unit")
        print(f"   Average periods per unit: {panel_info.mean():.1f}")
        
        if units_insufficient > 0:
            pct_insufficient = 100 * units_insufficient / len(panel_info)
            print(f"   ⚠️  Warning: Some units have ≤ 2 periods. Double demeaning requires T > 2.")
            print(f"   Consider filtering units with insufficient time variation.")
    
    def _apply_grand_mean_centering(self, df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
        """Apply grand mean centering to specified variables."""
        variables_to_center = [self.y_var, self.x_var, self.z_var] + self.w_vars
        
        for var in variables_to_center:
            if var in df.columns:
                original_mean = df[var].mean()
                df[var] = df[var] - original_mean
                if verbose:
                    print(f"  {var}: mean before = {original_mean:.5f}, mean after = {df[var].mean():.10f}")
        
        return df


def create_double_demeaned_interaction(df: pd.DataFrame, x_var: str, z_var: str, 
                                     unit_var: str, verbose: bool = True) -> pd.DataFrame:
    """
    Create double demeaned interaction term.
    
    This is the core innovation of Giesselmann & Schmidt-Catran (2022):
    1. First demean each variable within units
    2. Then create interaction from the demeaned variables
    
    Parameters
    ----------
    df : pd.DataFrame
        Panel data with MultiIndex [unit, time]
    x_var, z_var : str
        Names of interacting variables
    unit_var : str
        Unit identifier (used for grouping)
    verbose : bool, optional
        Whether to print detailed output
        
    Returns
    -------
    pd.DataFrame
        DataFrame with added demeaned variables and double-demeaned interaction
    """
    df_dd = df.copy()
    
    if verbose:
        print("="*80)
        print("CREATING DOUBLE DEMEANED INTERACTION")
        print("="*80)
        print("Step 1: Computing within-unit means...")
    
    # Step 1: Create within-unit means for each variable
    for var in [x_var, z_var]:
        mean_var_name = f'mean_{var}'
        df_dd[mean_var_name] = df_dd.groupby(level=0)[var].transform('mean')
        
        if verbose:
            print(f"  {var}: unit means calculated -> {mean_var_name}")
            print(f"    Example: Unit 1 mean = {df_dd[mean_var_name].iloc[0]:.5f}")
    
    # Step 2: Create demeaned variables (within-unit deviations)
    if verbose:
        print("\nStep 2: Creating within-unit demeaned variables...")
    
    for var in [x_var, z_var]:
        dm_var_name = f'dm_{var}'
        df_dd[dm_var_name] = df_dd[var] - df_dd[f'mean_{var}']
        
        if verbose:
            print(f"  {var} -> {dm_var_name} = {var} - mean_{var}")
            print(f"    Mean of demeaned var: {df_dd[dm_var_name].mean():.10f} (should be ≈ 0)")
            print(f"    Std of demeaned var: {df_dd[dm_var_name].std():.5f}")
    
    # Step 3: Create interaction terms
    dm_x = f'dm_{x_var}'
    dm_z = f'dm_{z_var}'
    interaction_name = f'int_{x_var}_{z_var}'
    dd_interaction_name = f'dd_{interaction_name}'
    
    # Standard interaction (X * Z)
    df_dd[interaction_name] = df_dd[x_var] * df_dd[z_var]
    
    # Double demeaned interaction (dm_X * dm_Z)  
    df_dd[dd_interaction_name] = df_dd[dm_x] * df_dd[dm_z]
    
    if verbose:
        print("\nStep 3: Creating double demeaned interaction...")
        print(f"  Double demeaned interaction: {dd_interaction_name} = {dm_x} * {dm_z}")
        print(f"  Mean of dd interaction: {df_dd[dd_interaction_name].mean():.10f}")
        print(f"  Std of dd interaction: {df_dd[dd_interaction_name].std():.5f}")
        
        correlation = df_dd[interaction_name].corr(df_dd[dd_interaction_name])
        print(f"  Correlation with standard interaction: {correlation:.5f}")
        
        print(f"\nFirst 5 observations comparison:")
        comparison_cols = [x_var, z_var, dm_x, dm_z, interaction_name, dd_interaction_name]
        print(df_dd[comparison_cols].head())
    
    return df_dd


def estimate_fe_models(df: pd.DataFrame, y_var: str, x_var: str, z_var: str, 
                      w_vars: List[str], verbose: bool = True) -> Tuple:
    """
    Estimate standard FE and double demeaned FE models and compare results.
    
    Parameters
    ----------
    df : pd.DataFrame
        Panel data with interaction terms created
    y_var : str
        Dependent variable name
    x_var, z_var : str
        Interacting variable names
    w_vars : List[str]
        Control variable names
    verbose : bool, optional
        Whether to print detailed output
        
    Returns
    -------
    Tuple[PanelResults, PanelResults, pd.DataFrame]
        Standard FE results, double demeaned FE results, comparison DataFrame
    """
    
    # Check within-unit variation and filter problematic controls
    if verbose:
        print("🔍 CHECKING WITHIN-UNIT VARIATION")
        print("="*50)
    
    all_vars = [y_var, x_var, z_var] + w_vars
    filtered_w_vars = []
    excluded_vars = set()
    
    for var in all_vars:
        if var in df.columns:
            variation_check = check_within_unit_variation(df, var)
            units_with_variation = variation_check['units_with_variation']
            total_units = variation_check['total_units']
            pct_variation = 100 * units_with_variation / total_units
            
            if verbose:
                print(f"  {var}: {units_with_variation}/{total_units} units have variation ({pct_variation:.1f}%)")
            
            if var in w_vars and pct_variation < 5.0:  # Less than 5% variation
                excluded_vars.add(var)
                if verbose:
                    print(f"    ❌ {var} excluded - insufficient within-unit variation for FE")
            elif var in w_vars:
                filtered_w_vars.append(var)
            elif pct_variation < 10.0 and verbose:
                print(f"    ⚠️  WARNING: {var} has limited within-unit variation")
    
    if excluded_vars and verbose:
        print(f"\n📋 SUMMARY: Excluded {excluded_vars} due to insufficient within-unit variation")
        print("   This is correct for FE models - they can't identify time-invariant effects")
    
    # Model specifications
    interaction_std = f'int_{x_var}_{z_var}'
    interaction_dd = f'dd_int_{x_var}_{z_var}'
    
    exog_vars_std = [x_var, z_var, interaction_std] + filtered_w_vars
    exog_vars_dd = [x_var, z_var, interaction_dd] + filtered_w_vars
    
    if verbose:
        print(f"\n🔧 Variables used in analysis:")
        print(f"   Dependent: {y_var}")
        print(f"   Interactors: {x_var} × {z_var}")
        print(f"   Controls: {filtered_w_vars}")
    
    # Estimate models with proper error handling
    try:
        # Standard FE model
        if verbose:
            print("\n" + "="*80)
            print("STANDARD FIXED EFFECTS MODEL")  
            print("="*80)
            print(f"Model: {y_var} ~ {x_var} + {z_var} + {interaction_std} + unit_fe")
            print(f"Standard interaction: {interaction_std} = {x_var} * {z_var}")
            print("\nNote: This is the conventional approach that may be biased")
            print("      when both variables vary within units.")
        
        standard_model = PanelOLS(df[y_var], df[exog_vars_std], entity_effects=True)
        standard_results = standard_model.fit(cov_type='clustered', cluster_entity=True, debiased=True)
        
        if verbose:
            print(standard_results.summary.tables[1])
        
        # Double demeaned FE model
        if verbose:
            print("\n" + "="*80)
            print("DOUBLE DEMEANED FIXED EFFECTS MODEL")
            print("="*80)
            print(f"Model: {y_var} ~ {x_var} + {z_var} + {interaction_dd} + unit_fe")
            print(f"Double demeaned interaction: {interaction_dd} = dm_{x_var} * dm_{z_var}")
            print("\nNote: This provides an unbiased within-unit interaction estimator")
            print("      that controls for unobserved effect heterogeneity.")
        
        dd_model = PanelOLS(df[y_var], df[exog_vars_dd], entity_effects=True)
        dd_results = dd_model.fit(cov_type='clustered', cluster_entity=True, debiased=True)
        
        if verbose:
            print(dd_results.summary.tables[1])
        
        # Create comparison table
        comparison_df = _create_comparison_table(
            standard_results, dd_results, x_var, z_var, verbose
        )
        
        return standard_results, dd_results, comparison_df
        
    except Exception as e:
        print(f"❌ Error in model estimation: {str(e)}")
        raise


def _create_comparison_table(standard_results, dd_results, x_var: str, z_var: str, 
                           verbose: bool) -> pd.DataFrame:
    """Create coefficient comparison table."""
    
    # Extract coefficients and standard errors
    std_params = standard_results.params
    std_se = standard_results.std_errors
    dd_params = dd_results.params  
    dd_se = dd_results.std_errors
    
    # Find common variables
    common_vars = list(set(std_params.index) & set(dd_params.index))
    if f'int_{x_var}_{z_var}' in std_params.index:
        common_vars.append('int_' + x_var + '_' + z_var)
        common_vars = [v for v in common_vars if v != f'int_{x_var}_{z_var}']
        common_vars.append(f'int_{x_var}_{z_var}')
    
    comparison_data = []
    for var in common_vars:
        if var in std_params.index and var in dd_params.index:
            comparison_data.append({
                'Variable': var,
                'Std FE Coef': std_params[var],
                'Std FE SE': std_se[var], 
                'DD Coef': dd_params[var] if var != f'int_{x_var}_{z_var}' else dd_params[f'dd_int_{x_var}_{z_var}'],
                'DD SE': dd_se[var] if var != f'int_{x_var}_{z_var}' else dd_se[f'dd_int_{x_var}_{z_var}'],
                'Difference': std_params[var] - (dd_params[var] if var != f'int_{x_var}_{z_var}' else dd_params[f'dd_int_{x_var}_{z_var}'])
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    if verbose and len(comparison_df) > 0:
        print("\n" + "="*80)
        print("MODEL COMPARISON")
        print("="*80)
        
        # Format the comparison table
        for _, row in comparison_df.iterrows():
            var_display = 'interaction' if 'int_' in row['Variable'] else row['Variable']
            print(f"{var_display:<12} {row['Std FE Coef']:>11.5f} {row['Std FE SE']:>9.5f} {row['DD Coef']:>11.5f} {row['DD SE']:>9.5f} {row['Difference']:>11.5f}")
        
        # Highlight key finding
        interaction_diff = comparison_df[comparison_df['Variable'].str.contains('int_')]['Difference']
        if len(interaction_diff) > 0:
            diff_val = interaction_diff.iloc[0]
            print(f"\n🎯 KEY FINDING - Interaction Effect:")
            print(f"   Difference in interaction coefficients: {diff_val:.6f}")
            if abs(diff_val) > 10:  # Substantial difference threshold
                print(f"   ⚠️  SUBSTANTIAL DIFFERENCE detected! Standard FE may be biased.")
            else:
                print(f"   ✅ Small difference - both estimators appear similar.")
    
    return comparison_df


def perform_hausman_test(standard_results, dd_results, x_var: str, z_var: str, 
                        verbose: bool = True) -> Optional[Dict]:
    """
    Perform Hausman test for systematic differences between estimators.
    
    Implements proper statistical testing including handling of 
    non-positive definite variance difference matrices.
    
    Parameters
    ----------
    standard_results : PanelResults
        Results from standard FE model
    dd_results : PanelResults  
        Results from double demeaned FE model
    x_var, z_var : str
        Variable names for interaction
    verbose : bool, optional
        Whether to print detailed output
        
    Returns
    -------
    Optional[Dict]
        Dictionary with test results or None if test fails
    """
    
    try:
        if verbose:
            print("="*80)
            print("HAUSMAN TEST FOR SYSTEMATIC DIFFERENCES")
            print("="*80)
            print("Null Hypothesis: No systematic difference between Standard FE and Double Demeaned estimators")
            print("Alternative: Standard FE estimator is biased due to unobserved effect heterogeneity")
        
        # Get coefficients and variance matrices
        b_std = standard_results.params
        b_dd = dd_results.params
        V_std = standard_results.cov
        V_dd = dd_results.cov
        
        # Map interaction variable name
        interaction_std_name = f'int_{x_var}_{z_var}'
        interaction_dd_name = f'dd_int_{x_var}_{z_var}'
        
        # Find common variables and handle interaction mapping
        common_vars = []
        b_std_mapped = []
        b_dd_mapped = []
        V_std_mapped = []
        V_dd_mapped = []
        
        for var in b_std.index:
            if var == interaction_std_name and interaction_dd_name in b_dd.index:
                common_vars.append(var)
                b_std_mapped.append(b_std[var])
                b_dd_mapped.append(b_dd[interaction_dd_name])
            elif var in b_dd.index and var != interaction_std_name:
                common_vars.append(var)
                b_std_mapped.append(b_std[var])
                b_dd_mapped.append(b_dd[var])
        
        if len(common_vars) == 0:
            print("❌ No common coefficients found for Hausman test")
            return None
        
        # Extract corresponding variance submatrices
        std_indices = [b_std.index.get_loc(var) if var != interaction_std_name 
                      else b_std.index.get_loc(interaction_std_name) for var in common_vars]
        dd_indices = [b_dd.index.get_loc(var) if var != interaction_std_name 
                     else b_dd.index.get_loc(interaction_dd_name) for var in common_vars]
        
        V_std_sub = V_std.iloc[std_indices, std_indices].values
        V_dd_sub = V_dd.iloc[dd_indices, dd_indices].values
        
        # Convert to numpy arrays
        b_std_vec = np.array(b_std_mapped)
        b_dd_vec = np.array(b_dd_mapped)
        
        if verbose:
            print(f"\nTesting {len(common_vars)} common coefficients: {common_vars}")
        
        # Calculate difference and variance difference (dd_IE - FE_IE convention: b - B)
        diff = b_dd_vec - b_std_vec  # dd_IE is consistent (b), FE_IE is efficient (B)
        V_diff = V_dd_sub - V_std_sub
        
        # Check positive definiteness and compute test statistic
        eigenvals = np.linalg.eigvals(V_diff)  
        pos_def = np.all(eigenvals > 1e-10)
        
        if verbose:
            print("\n                ---- Coefficients ----")
            print("             |      (b)          (B)            (b-B)     sqrt(diag(V_b-V_B))")
            print("             |     dd_IE        FE_IE        Difference       Std. err.")
            print("-------------+----------------------------------------------------------------")
            
            for i, var in enumerate(common_vars):
                var_display = var[:12] if len(var) <= 12 else var[:9] + "~" + var[-2:]
                
                # Handle standard errors - show "." when unreliable
                if not pos_def and V_diff[i,i] <= 0:
                    se_display = "        ."
                else:
                    se_diff = np.sqrt(abs(V_diff[i,i])) if V_diff[i,i] != 0 else 0
                    se_display = f"{se_diff:>11.4f}"
                
                print(f"{var_display:>12} | {b_dd_vec[i]:>11.5f}   {b_std_vec[i]:>11.5f}   {diff[i]:>11.5f}   {se_display}")
            
            print("------------------------------------------------------------------------------")
            print("                          b = Consistent under H0 and Ha; obtained from dd_IE.")
            print("           B = Inconsistent under Ha, efficient under H0; obtained from FE_IE.")
        
        # Compute test statistic with proper handling of non-positive definite matrices
        if pos_def:
            try:
                V_diff_inv = np.linalg.inv(V_diff)
                hausman_stat = diff.T @ V_diff_inv @ diff
            except np.linalg.LinAlgError:
                pos_def = False
        
        if not pos_def:
            # Use multiple numerical approaches for robust estimation
            try:
                # Approach 1: Eigendecomposition
                eigenvals, eigenvecs = np.linalg.eigh(V_diff)
                max_eigenval = np.max(np.abs(eigenvals))
                tolerance = max_eigenval * len(V_diff) * np.finfo(float).eps
                valid_mask = eigenvals > tolerance
                
                if np.sum(valid_mask) > 0:
                    eigenvals_pos = eigenvals[valid_mask]
                    eigenvecs_pos = eigenvecs[:, valid_mask]
                    V_diff_ginv = eigenvecs_pos @ np.diag(1/eigenvals_pos) @ eigenvecs_pos.T
                    hausman_stat_1 = diff.T @ V_diff_ginv @ diff
                else:
                    hausman_stat_1 = np.inf
                
                # Approach 2: SVD with different tolerance
                U, s, Vh = np.linalg.svd(V_diff, full_matrices=False)
                tolerance_2 = np.max(s) * 1e-10
                s_inv = np.where(s > tolerance_2, 1/s, 0)
                V_diff_ginv_2 = (Vh.T * s_inv) @ Vh
                hausman_stat_2 = diff.T @ V_diff_ginv_2 @ diff
                
                # Choose the more stable result
                if hausman_stat_1 != np.inf and not np.isnan(hausman_stat_1):
                    hausman_stat = float(hausman_stat_1)
                else:
                    hausman_stat = float(hausman_stat_2)
                
                # Final fallback
                if hausman_stat < 0 or hausman_stat > 100:
                    V_diff_ginv = np.linalg.pinv(V_diff, rcond=1e-10)
                    hausman_stat = float(diff.T @ V_diff_ginv @ diff)
                    
            except Exception as e:
                print(f"❌ Cannot compute Hausman statistic - numerical issues: {e}")
                return None
        
        # Degrees of freedom and p-value
        df = len(common_vars)
        p_value = 1 - stats.chi2.cdf(hausman_stat, df=df)
        
        if verbose:
            print(f"\nTest of H0: Difference in coefficients not systematic")
            print(f"")
            print(f"    chi2({df}) = (b-B)'[(V_b-V_B)^(-1)](b-B)")
            print(f"            = {hausman_stat:>6.2f}")
            print(f"Prob > chi2 = {p_value:.4f}")
            if not pos_def:
                print(f"(V_b-V_B is not positive definite)")
            
            # Interpretation
            print(f"\n📋 INTERPRETATION:")
            if p_value < 0.05:
                print(f"   🚨 REJECT null hypothesis at 5% level (p = {p_value:.4f} < 0.05)")
                print(f"   → Evidence of systematic differences between estimators")
                print(f"   → Standard FE may be inconsistent - prefer double demeaned estimator")
                conclusion = "SYSTEMATIC BIAS DETECTED"
            else:
                print(f"   ✅ FAIL TO REJECT null hypothesis at 5% level (p = {p_value:.4f} ≥ 0.05)")
                print(f"   → No systematic differences detected")
                print(f"   → Both estimators appear consistent; standard FE is more efficient")
                conclusion = "NO SYSTEMATIC BIAS"
            
            if not pos_def:
                print(f"\n📝 NOTE: The variance matrix difference is not positive definite.")
                print(f"   This can occur with small samples or high collinearity.")
                print(f"   Test statistic computed using generalized inverse: chi2({df}) = {hausman_stat:.2f}, p = {p_value:.4f}")
        
        return {
            'hausman_statistic': hausman_stat,
            'p_value': p_value,
            'degrees_of_freedom': df,
            'coefficient_differences': diff,
            'conclusion': conclusion,
            'positive_definite': pos_def
        }
        
    except Exception as e:
        if verbose:
            print(f"❌ Error in Hausman test: {str(e)}")
        return None
