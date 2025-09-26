"""
Tests for core functionality of dd_ie package.
"""

import pandas as pd
import numpy as np
import pytest
from dd_ie import DoubleDemeanAnalysis, create_double_demeaned_interaction


class TestDoubleDemeanAnalysis:
    """Test cases for DoubleDemeanAnalysis class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        # Create simple test data
        np.random.seed(42)
        n_units, n_time = 10, 5
        data = []
        
        for unit in range(1, n_units + 1):
            for time in range(1, n_time + 1):
                data.append({
                    'unit_id': unit,
                    'time_id': time,
                    'y': np.random.normal(0, 1),
                    'x': np.random.normal(0, 1),
                    'z': np.random.normal(0, 1),
                    'control1': np.random.normal(0, 1)
                })
        
        df = pd.DataFrame(data)
        
        # Initialize analysis
        analysis = DoubleDemeanAnalysis(
            data=df,
            unit_var='unit_id',
            time_var='time_id',
            y_var='y',
            x_var='x',
            z_var='z',
            w_vars=['control1']
        )
        
        assert analysis.unit_var == 'unit_id'
        assert analysis.time_var == 'time_id'
        assert analysis.y_var == 'y'
        assert analysis.x_var == 'x'
        assert analysis.z_var == 'z'
        assert analysis.w_vars == ['control1']
        assert len(analysis.data) == n_units * n_time
    
    def test_missing_variables(self):
        """Test error handling for missing variables."""
        # Create data missing required variables
        df = pd.DataFrame({
            'unit_id': [1, 1, 2, 2],
            'time_id': [1, 2, 1, 2],
            'y': [1, 2, 3, 4]
        })
        
        with pytest.raises(KeyError):
            DoubleDemeanAnalysis(
                data=df,
                unit_var='unit_id',
                time_var='time_id',
                y_var='y',
                x_var='missing_x',  # This variable doesn't exist
                z_var='missing_z',  # This variable doesn't exist
            )


class TestCreateDoubleDemeanedInteraction:
    """Test cases for create_double_demeaned_interaction function."""
    
    def test_basic_functionality(self):
        """Test basic double demeaning functionality."""
        # Create simple test data
        data = pd.DataFrame({
            'unit_id': [1, 1, 1, 2, 2, 2],
            'time_id': [1, 2, 3, 1, 2, 3],
            'x': [1, 2, 3, 4, 5, 6],
            'z': [2, 4, 6, 1, 3, 5]
        })
        
        # Set index
        data = data.set_index(['unit_id', 'time_id'])
        
        # Apply double demeaning
        result = create_double_demeaned_interaction(
            data, 'x', 'z', 'unit_id', verbose=False
        )
        
        # Check that required columns were created
        expected_cols = ['x', 'z', 'mean_x', 'mean_z', 'dm_x', 'dm_z', 
                        'int_x_z', 'dd_int_x_z']
        for col in expected_cols:
            assert col in result.columns, f"Column {col} not found"
        
        # Check that demeaned variables have zero mean within units
        for unit in result.index.get_level_values(0).unique():
            unit_data = result.loc[unit]
            assert abs(unit_data['dm_x'].mean()) < 1e-10
            assert abs(unit_data['dm_z'].mean()) < 1e-10
    
    def test_interaction_calculation(self):
        """Test that interactions are calculated correctly."""
        # Create simple test data
        data = pd.DataFrame({
            'unit_id': [1, 1, 2, 2],
            'time_id': [1, 2, 1, 2],
            'x': [1, 3, 2, 4],  # Unit 1 mean = 2, Unit 2 mean = 3
            'z': [2, 4, 1, 3]   # Unit 1 mean = 3, Unit 2 mean = 2
        })
        
        data = data.set_index(['unit_id', 'time_id'])
        
        result = create_double_demeaned_interaction(
            data, 'x', 'z', 'unit_id', verbose=False
        )
        
        # Manually verify calculations for unit 1
        unit1_data = result.loc[1]
        
        # x values: [1, 3], mean = 2, demeaned = [-1, 1]
        # z values: [2, 4], mean = 3, demeaned = [-1, 1]
        # dd interaction should be: [-1 * -1, 1 * 1] = [1, 1]
        
        expected_dd_interaction = np.array([1.0, 1.0])
        actual_dd_interaction = unit1_data['dd_int_x_z'].values
        
        np.testing.assert_array_almost_equal(actual_dd_interaction, expected_dd_interaction)


if __name__ == '__main__':
    pytest.main([__file__])
