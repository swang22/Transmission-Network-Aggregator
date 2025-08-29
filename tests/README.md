# Tests

This folder contains unit tests for the transmission network analysis toolkit.

## Running Tests

To run the basic tests:
```bash
python tests/test_basic.py
```

To run with pytest (if installed):
```bash
python -m pytest tests/
```

## Current Test Structure

### `test_basic.py`
Basic functionality tests that work reliably in CI:
- `test_pandas_available()`: Verify pandas installation
- `test_src_directory_exists()`: Check core module files exist  
- `test_basic_python_functionality()`: Test basic data operations

These tests are designed to be minimal, fast, and work without requiring full geospatial dependencies.

## Future Test Development

Additional test files can be added for:
- **Aggregation functions**: Bus-to-county mapping, AC/HVDC aggregation
- **Visualization functions**: Map generation, capacity classification
- **Data loading**: MATPOWER and counties data loading

## Test Data

For comprehensive testing, small sample datasets could be added:
- Sample bus/branch/substation data
- Sample county boundaries
- Expected output examples

## Coverage Goals

- Core functions: Focus on critical path testing
- Edge cases: Handle missing data, invalid inputs  
- CI compatibility: Tests that work across environments

## Continuous Integration

Tests are automatically run on:
- Every push to main branch
- All pull requests
- Multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Multiple platforms (Windows, Linux, macOS)
