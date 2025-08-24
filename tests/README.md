# Tests

This folder contains unit tests for the transmission network analysis toolkit.

## Running Tests

To run all tests:
```bash
python -m pytest tests/
```

To run tests with coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Structure

### `test_aggregation.py`
Tests for core aggregation functions:
- `test_build_bus_lookup()`: Bus-to-county mapping
- `test_aggregate_ac()`: AC line aggregation
- `test_aggregate_hvdc()`: HVDC line aggregation
- `test_duplicate_handling()`: Duplicate column handling

### `test_visualization.py` 
Tests for visualization functions:
- `test_create_transmission_map()`: Map generation
- `test_capacity_classes()`: Capacity classification
- `test_regional_filtering()`: Geographic filtering

### `test_data_loading.py`
Tests for data loading functions:
- `test_load_grid_tables()`: MATPOWER data loading
- `test_load_counties()`: Counties shapefile loading
- `test_data_validation()`: Input data validation

## Test Data

Small test datasets are provided in `tests/data/`:
- `test_bus.csv`: Sample bus data
- `test_branch.csv`: Sample branch data  
- `test_counties.geojson`: Sample county boundaries

## Coverage Goals

- Core functions: 90%+ coverage
- Edge cases: Handle missing data, invalid inputs
- Integration: End-to-end pipeline testing

## Continuous Integration

Tests are automatically run on:
- Every push to main branch
- All pull requests
- Multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Multiple platforms (Windows, Linux, macOS)
