"""
setup.py
--------
Package setup for transmission network analysis toolkit.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README_new.md").read_text(encoding='utf-8')

setup(
    name="transmission-network-analysis",
    version="1.0.0",
    author="Shen Wang",
    author_email="shen.wang@mit.edu",
    description="A toolkit for aggregating and visualizing electricity transmission networks at the county level",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/transmission-network-analysis",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.5.0",
        "geopandas>=0.12.0", 
        "matplotlib>=3.5.0",
        "plotly>=5.0.0",
        "shapely>=1.8.0",
        "pyproj>=3.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "run-transmission=src.run_transmission:main",
            "visualize-transmission=src.visualize_transmission:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
