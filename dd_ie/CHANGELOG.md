# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-26

### Added
- Initial public release of dd_ie package
- `DoubleDemeanAnalysis` class for complete double demeaning workflow
- Core functions: `create_double_demeaned_interaction`, `estimate_fe_models`, `perform_hausman_test`
- Utility functions for panel data validation and preparation
- Comprehensive statistical testing with Hausman test
- Robust handling of edge cases (non-positive definite matrices, insufficient variation)
- Publication-ready output with clear interpretation
- Complete test suite with pytest
- MIT license

### Features
- **Double Demeaning Implementation**: Unbiased within-unit interaction estimator
- **Statistical Testing**: Hausman test for systematic differences between estimators
- **Data Validation**: Automatic checking of panel structure and within-unit variation
- **Error Handling**: Robust numerical approaches for matrix operations
- **Clear Output**: Step-by-step analysis with detailed results and interpretation

### Dependencies
- pandas >= 1.3.0
- numpy >= 1.20.0
- scipy >= 1.7.0
- linearmodels >= 4.0.0

### Optional Dependencies
- matplotlib >= 3.5.0 (for visualization)
- seaborn >= 0.11.0 (for visualization)
- pytest >= 6.0 (for development/testing)

### Documentation
- Comprehensive README with examples
- Complete API documentation with docstrings
- Mathematical background and methodology
- Installation and usage instructions

## References

This implementation is based on:

**Giesselmann, M., & Schmidt-Catran, A. W. (2022). Interactions in Fixed Effects Regression Models. *Sociological Methods & Research*, 51(3), 1100-1127.**
