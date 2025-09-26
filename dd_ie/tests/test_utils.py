"""
Tests for utility functions of dd_ie package.
"""

import pandas as pd
import numpy as np
import pytest
from dd_ie.utils import (
    validate_panel_data, 
    check_within_unit_variation,
    prepare_panel_data,
    filter_units_by_time_periods
)


class TestValidatePanelData:
    """Test cases for validate_panel_data function."""
    
    def test_valid_panel_data(self):
        """Test validation of valid panel data."""
        data = pd.DataFrame({
            'unit_id': [1, 1, 2, 2, 3, 3],
            'time_id': [1, 2, 1, 2, 1, 2],
            'value': [10, 20, 30, 40, 50, 60]
        })
        
        result = validate_panel_data(data, 'unit_id', 'time_id')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 6
        assert 'unit_id' in result.columns
        assert 'time_id' in result.columns
    
    def test_missing_unit_variable(self):
        """Test error when unit variable is missing."""
        data = pd.DataFrame({
            'time_id': [1, 2, 1, 2],
            'value': [10, 20, 30, 40]
        })
        
        with pytest.raises(ValueError, match="Required columns missing"):
            validate_panel_data(data, 'missing_unit', 'time_id')
    
    def test_missing_time_variable(self):
        """Test error when time variable is missing."""
        data = pd.DataFrame({
            'unit_id': [1, 1, 2, 2],
            'value': [10, 20, 30, 40]
        })
        
        with pytest.raises(ValueError, match="Required columns missing"):
            validate_panel_data(data, 'unit_id', 'missing_time')
    
    def test_missing_values_in_id_variables(self):
        """Test error when ID variables have missing values."""
        data = pd.DataFrame({
            'unit_id': [1, 1, None, 2],
            'time_id': [1, 2, 1, 2],
            'value': [10, 20, 30, 40]
        })
        
        with pytest.raises(ValueError, match="Missing values found in unit variable"):
            validate_panel_data(data, 'unit_id', 'time_id')


class TestCheckWithinUnitVariation:
    """Test cases for check_within_unit_variation function."""
    
    def test_variable_with_variation(self):
        """Test variable with within-unit variation."""
        data = pd.DataFrame({
            'unit_id': [1, 1, 1, 2, 2, 2],
            'time_id': [1, 2, 3, 1, 2, 3],
            'variable': [1, 2, 3, 4, 5, 6]  # Clear variation within units
        })
        data = data.set_index(['unit_id', 'time_id'])
        
        result = check_within_unit_variation(data, 'variable')
        
        assert result['variable'] == 'variable'
        assert result['total_units'] == 2
        assert result['units_with_variation'] == 2
        assert result['units_without_variation'] == 0
        assert result['pct_with_variation'] == 1.0
        assert result['meets_threshold'] == True
    
    def test_variable_without_variation(self):
        """Test variable with no within-unit variation."""
        data = pd.DataFrame({
            'unit_id': [1, 1, 1, 2, 2, 2],
            'time_id': [1, 2, 3, 1, 2, 3],
            'variable': [1, 1, 1, 2, 2, 2]  # No variation within units
        })
        data = data.set_index(['unit_id', 'time_id'])
        
        result = check_within_unit_variation(data, 'variable')
        
        assert result['units_with_variation'] == 0
        assert result['units_without_variation'] == 2
        assert result['pct_with_variation'] == 0.0
        assert result['meets_threshold'] == False
    
    def test_missing_variable(self):
        """Test handling of missing variable."""
        data = pd.DataFrame({
            'unit_id': [1, 1, 2, 2],
            'time_id': [1, 2, 1, 2],
            'other_var': [1, 2, 3, 4]
        })
        data = data.set_index(['unit_id', 'time_id'])
        
        result = check_within_unit_variation(data, 'missing_variable')
        
        assert 'error' in result
        assert 'not found' in result['error']


class TestFilterUnitsByTimePeriods:
    """Test cases for filter_units_by_time_periods function."""
    
    def test_filtering_units(self):
        """Test filtering units by minimum time periods."""
        data = pd.DataFrame({
            'unit_id': [1, 1, 1, 2, 2, 3],  # Unit 1: 3 periods, Unit 2: 2 periods, Unit 3: 1 period
            'time_id': [1, 2, 3, 1, 2, 1],
            'value': [10, 20, 30, 40, 50, 60]
        })
        
        # Filter requiring minimum 3 periods
        result = filter_units_by_time_periods(data, 'unit_id', min_periods=3)
        
        # Only unit 1 should remain
        assert len(result) == 3
        assert result['unit_id'].nunique() == 1
        assert result['unit_id'].iloc[0] == 1
    
    def test_no_filtering_needed(self):
        """Test when no filtering is needed."""
        data = pd.DataFrame({
            'unit_id': [1, 1, 1, 2, 2, 2],  # Both units have 3 periods
            'time_id': [1, 2, 3, 1, 2, 3],
            'value': [10, 20, 30, 40, 50, 60]
        })
        
        # Filter requiring minimum 3 periods
        result = filter_units_by_time_periods(data, 'unit_id', min_periods=3)
        
        # All units should remain
        assert len(result) == len(data)
        assert result['unit_id'].nunique() == 2


if __name__ == '__main__':
    pytest.main([__file__])
