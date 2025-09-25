"""
Double Demeaning for Fixed Effects Interactions

A Python implementation of the double demeaning technique for proper estimation 
of interactions in fixed effects regression models.

Reference:
Giesselmann, M., & Schmidt-Catran, A. W. (2022). Interactions in Fixed Effects 
Regression Models. Sociological Methods & Research, 51(3), 1100-1127.
"""

from .core import (
    DoubleDemeanAnalysis,
    create_double_demeaned_interaction,
    estimate_fe_models,
    perform_hausman_test
)

from .utils import (
    validate_panel_data,
    check_within_unit_variation,
    prepare_panel_data
)

__version__ = "1.0.0"
__author__ = "Converted from Stata implementation by Nikolaos Koutounidis"
__email__ = "nikolaos.koutounidis@ugent.be"

__all__ = [
    'DoubleDemeanAnalysis',
    'create_double_demeaned_interaction',
    'estimate_fe_models', 
    'perform_hausman_test',
    'validate_panel_data',
    'check_within_unit_variation',
    'prepare_panel_data'
]
