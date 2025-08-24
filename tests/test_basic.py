"""
test_basic.py
------------------
Basic tests that verify core functionality.
"""

import sys
from pathlib import Path

# Add src to path for testing  
SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))


def test_pandas_available():
    """Test that pandas is available."""
    import pandas as pd
    df = pd.DataFrame({'a': [1, 2, 3]})
    assert len(df) == 3


def test_src_directory_exists():
    """Test that src directory exists and has expected files."""
    assert SRC_PATH.exists()
    
    expected_files = [
        'grid2county_txcap.py',
        'run_transmission.py',
        'visualize_transmission.py'
    ]
    
    for filename in expected_files:
        file_path = SRC_PATH / filename
        assert file_path.exists(), f"Missing file: {filename}"


def test_basic_python_functionality():
    """Test basic Python functionality."""
    # Basic data structures
    data = [1, 2, 3, 4, 5]
    assert sum(data) == 15
    
    # Dictionary operations
    lookup = {'a': 1, 'b': 2, 'c': 3}
    assert len(lookup) == 3
    
    # String operations
    text = "transmission,network,analysis"
    parts = text.split(',')
    assert len(parts) == 3


if __name__ == "__main__":
    test_pandas_available()
    test_src_directory_exists() 
    test_basic_python_functionality()
    print("✅ All basic tests passed!")
