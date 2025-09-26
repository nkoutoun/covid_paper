# Double Demeaning for Fixed Effects Interactions

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python implementation of the double demeaning technique for unbiased estimation of interactions in fixed effects models.

Translation by Nikolaos Koutounidis

## Reference

**Giesselmann, M., & Schmidt-Catran, A. W. (2022). Interactions in Fixed Effects Regression Models. *Sociological Methods & Research*, 51(3), 1100-1127.**

## The Problem & Solution

Standard fixed effects interactions (`X×Z`) may be biased when both variables vary within units and correlate with unobserved unit-specific moderators.

**Double demeaning** provides an unbiased within-unit interaction estimator by:
1. First demeaning each variable within units: `X* = X - X̄ᵢ`, `Z* = Z - Z̄ᵢ`
2. Then creating the interaction: `X* × Z*`

## Installation

```bash
# Install from source (development)
pip install git+https://github.com/nkoutoun/covid_paper.git#subdirectory=dd_ie

# Or clone and install locally
git clone https://github.com/nkoutoun/covid_paper.git
cd covid_paper/dd_ie
pip install .

# For development with optional dependencies
pip install .[dev,viz]
```

## Quick Start

```python
import pandas as pd
from dd_ie import DoubleDemeanAnalysis

# Load panel data  
df = pd.read_csv('your_data.csv')  # or pd.read_stata(), etc.

# Run analysis
analysis = DoubleDemeanAnalysis(
    data=df,
    unit_var='unit_id',      # Unit identifier
    time_var='time_id',      # Time identifier  
    y_var='outcome',         # Dependent variable
    x_var='treatment',       # First interacting variable
    z_var='moderator',       # Second interacting variable
    w_vars=['control1']      # Control variables (optional)
)

results = analysis.run_analysis()
```

## Key Features

- **Complete workflow**: Data validation → double demeaning → model estimation → statistical testing
- **Hausman test**: Detects systematic differences between estimators
- **Robust handling**: Manages edge cases and non-positive definite matrices
- **Clear output**: Publication-ready results with interpretation

## Model Comparison

### Standard FE (potentially biased)
```
Y = β₁X + β₂Z + β₃(X×Z) + γW + αᵢ + ε
```

### Double Demeaned FE (unbiased)
```
Y = β₁X + β₂Z + β₃(X*×Z*) + γW + αᵢ + ε
where X* = X - X̄ᵢ, Z* = Z - Z̄ᵢ
```

## Results Interpretation

- **Hausman Test p ≥ 0.05**: No systematic bias; standard FE is efficient
- **Hausman Test p < 0.05**: Systematic bias detected; prefer double demeaned estimator

## Data Requirements

- **Panel structure**: Unit and time identifiers
- **Minimum periods**: T > 2 per unit for identification  
- **Within-unit variation**: Both X and Z must vary within units
- **Format**: Long format with one row per unit-time observation

## Advanced Usage

```python
# Step-by-step analysis
from dd_ie import create_double_demeaned_interaction, estimate_fe_models, perform_hausman_test

df_processed = create_double_demeaned_interaction(df, 'x_var', 'z_var', 'unit_id')
standard_results, dd_results, comparison = estimate_fe_models(df_processed, 'y_var', 'x_var', 'z_var', ['control1'])
hausman_results = perform_hausman_test(standard_results, dd_results, 'x_var', 'z_var')
```

## Examples and Testing

- **Example Script**: See `examples/basic_example.py` for a complete working example with synthetic data
- **Test Suite**: Run tests with `pytest tests/` to verify installation
- **Documentation**: All functions include comprehensive docstrings

## Common Issues

- **"AbsorbingEffectError"**: Control variables with no within-unit variation (automatically filtered)
- **"Insufficient time periods"**: Filter units with T ≤ 2 before analysis
- **Non-positive definite matrix**: Use generalized inverse (handled automatically)

## When to Use

Use double demeaning when:
- Both interacting variables vary within units
- T > 2 time periods available
- Concerned about unobserved effect heterogeneity
- Hausman test suggests bias

## License

MIT License