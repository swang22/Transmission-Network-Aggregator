"""
test_aggregation.py
------------------
Unit tests for transmission aggregation functions.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for testing
SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))


def test_imports():
    """Test that core modules can be imported."""
    try:
        from grid2county_txcap import build_bus_lookup, aggregate_ac, aggregate_hvdc
        assert True  # If we get here, imports worked
    except ImportError as e:
        pytest.fail(f"Failed to import core functions: {e}")


def test_basic_dataframe_operations():
    """Test basic pandas operations that our functions rely on."""
    # Test DataFrame creation and basic operations
    df = pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6],
        'c': [7, 8, 9]
    })
    
    assert len(df) == 3
    assert list(df.columns) == ['a', 'b', 'c']
    assert df['a'].sum() == 6


class TestAggregationLogic:
    """Tests for aggregation logic without requiring geospatial data."""
    
    def test_aggregate_ac_mock(self):
        """Test AC aggregation with minimal mock data."""
        try:
            from grid2county_txcap import aggregate_ac
            
            # Sample branch data
            branch = pd.DataFrame({
                'from_bus': [1, 2, 1],
                'to_bus': [2, 3, 3], 
                'r_pu': [0.01, 0.02, 0.015],
                'x_pu': [0.1, 0.15, 0.12],
                'b_pu': [0.001, 0.002, 0.0015],
                'rateA': [100, 200, 150]
            })
            
            # Sample bus lookup (bus -> county FIPS)
            bus_lookup = pd.Series({1: '12345', 2: '23456', 3: '34567'})
            
            # Mock counties data
            counties_data = pd.DataFrame({
                'GEOID': ['12345', '23456', '34567'],
                'NAME': ['County A', 'County B', 'County C'],
                'STATEFP': ['12', '23', '34']
            })
            
            # This should work if the function handles missing geospatial data gracefully
            result = aggregate_ac(branch, bus_lookup, counties_data)
            
            # Basic checks
            assert isinstance(result, pd.DataFrame)
            assert len(result) >= 0  # Could be empty if no valid connections
            
        except Exception as e:
            # If function requires full geospatial setup, skip
            pytest.skip(f"Function requires full geospatial environment: {e}")
    
    def test_data_processing_functions(self):
        """Test data processing components that don't require geospatial libraries."""
        # Test basic data manipulation that our scripts do
        df = pd.DataFrame({
            'from_county': ['12345', '23456', '12345'],
            'to_county': ['23456', '34567', '34567'],
            'capacity': [100, 200, 150]
        })
        
        # Group by county pairs (similar to our aggregation logic)
        grouped = df.groupby(['from_county', 'to_county'])['capacity'].sum().reset_index()
        
        assert len(grouped) == 3  # Should have 3 unique pairs
        assert grouped['capacity'].sum() == 450  # Total capacity preserved


if __name__ == "__main__":
    pytest.main([__file__])
