# Contributing to Transmission Network Analysis

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/transmission-network-analysis.git
   cd transmission-network-analysis
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]  # Install development dependencies
   ```

## Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** and test them
3. **Run tests**:
   ```bash
   python -m pytest tests/
   ```
4. **Check code style**:
   ```bash
   black src/ tests/
   flake8 src/ tests/
   ```
5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request** on GitHub

## Types of Contributions

### Bug Reports
- Use the GitHub issue tracker
- Include Python version, OS, and package versions
- Provide minimal reproducible example
- Include error messages and stack traces

### Feature Requests
- Describe the use case and benefits
- Provide examples of desired behavior
- Consider implementation complexity

### Code Contributions
- **New aggregation methods**: Support for other grid data formats
- **Visualization enhancements**: New plot types, styling options
- **Performance improvements**: Faster algorithms, memory optimization
- **Documentation**: Improve docstrings, tutorials, examples

## Code Style

- **Python**: Follow PEP 8
- **Formatting**: Use `black` with default settings
- **Linting**: Pass `flake8` checks
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings

### Example:
```python
def aggregate_transmission(
    branch: pd.DataFrame, 
    bus_lookup: pd.Series,
    power_factor: float = 0.97
) -> pd.DataFrame:
    """Aggregate transmission lines between counties.
    
    Args:
        branch: Branch data from MATPOWER dataset
        bus_lookup: Mapping from bus ID to county FIPS
        power_factor: Power factor for MVA to MW conversion
        
    Returns:
        DataFrame with aggregated transmission edges
        
    Raises:
        ValueError: If bus_lookup is incomplete
    """
    pass
```

## Testing Guidelines

- **Unit tests**: Test individual functions
- **Integration tests**: Test end-to-end workflows
- **Coverage**: Aim for >90% test coverage
- **Data**: Use small test datasets, not full grid files

### Test Structure:
```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = create_test_data()
    
    # Act  
    result = function_under_test(input_data)
    
    # Assert
    assert result.shape == expected_shape
    assert result.columns.tolist() == expected_columns
```

## Documentation

- **README**: Keep updated with new features
- **API docs**: Document all public functions
- **Examples**: Add practical usage examples
- **Tutorials**: Create Jupyter notebooks for complex workflows

## Git Commit Messages

Use conventional commit format:
- `feat: add HVDC visualization support`
- `fix: handle missing zone names gracefully`
- `docs: update installation instructions`
- `test: add unit tests for capacity aggregation`
- `refactor: simplify bus lookup logic`

## Release Process

1. Update version in `setup.py` and `src/__init__.py`
2. Update `CHANGELOG.md` with new features/fixes
3. Create release branch: `release/v1.1.0`
4. Run full test suite
5. Create GitHub release with tag
6. Merge to main branch

## Questions?

- Open an issue for technical questions
- Email maintainers for sensitive topics
- Check existing issues before creating new ones

Thank you for contributing!
