# Transmission Network Analysis

A Python toolkit for aggregating and visualizing electricity transmission networks at the county level from MATPOWER-style grid datasets. Built using the comprehensive **USA Test System** dataset (Xu et al., 2021) from Zenodo.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🔧 Features

- **Transmission Aggregation**: Convert MATPOWER bus/branch data to county-level transmission edges
- **HVDC Support**: Analyze both AC and HVDC transmission lines
- **Geospatial Mapping**: Create detailed maps with capacity-based line visualization
- **Interactive Visualizations**: Generate interactive HTML maps with hover details
- **Regional Filtering**: Focus on specific states, zones, or interconnects
- **Capacity Classes**: Visual distinction across 6 capacity ranges (<200MW to 5K+MW)

## 📊 Dataset Overview

The processed dataset contains **7,652 transmission edges** with:
- **7,637 AC transmission lines**
- **15 HVDC transmission lines**
- **21 data columns** including geographic, network, and capacity information
- **Complete US coverage** across Eastern, Western, and Texas interconnects

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/swang22/Transmission-Network-Aggregator.git
cd Transmission-Network-Aggregator
pip install -r requirements.txt
```

### 2. Data Preparation

This toolkit uses the **USA Test System** dataset from Zenodo:

> **Xu, B., Dvorkin, Y., Kirschen, D. S., Silva-Monroy, C. A., & Watson, J. P. (2021).** 
> *A Synthetic Time-Variant U.S. Power Grid Data Set for the Evaluation of Variable Generation and Demand Response*. 
> Zenodo. https://doi.org/10.5281/zenodo.4538590

The dataset provides a comprehensive synthetic representation of the U.S. power grid with time-variant generation and demand data. For transmission analysis, we use the network topology files:

```bash
# The base_grid folder should contain:
# - bus.csv, branch.csv, sub.csv, bus2sub.csv
# - dcline.csv (for HVDC), zone.csv
```

**Dataset Features:**
- **82,000+ buses** representing generation and load points
- **104,000+ transmission branches** with detailed electrical parameters  
- **Geographic mapping** to U.S. counties via substations
- **Three interconnects**: Eastern, Western, and Texas (ERCOT)
- **Voltage levels**: From distribution (4kV) to transmission (765kV)

**To download the original dataset:**
1. Visit: https://zenodo.org/records/4538590
2. Download the `USATestSystem.zip` file (~4.2 GB)
3. Extract the network data files to the `data/base_grid/` folder

*Note: The repository includes a cleaned subset focused on transmission analysis (49 MB vs 4.2 GB).*

### 3. Generate Transmission Data

```bash
python src/run_transmission.py
```

This creates `outputs/county_edges_tx.csv` with all transmission edges.

### 4. Create Visualizations

```bash
# Texas transmission network
python src/visualize_transmission.py --region "TX" --type state --output outputs/texas.png

# Interactive California map
python src/visualize_transmission.py --region "CA" --type state --output outputs/california.html --interactive

# Western Interconnect overview
python src/visualize_transmission.py --region "Western" --type interconnect --output outputs/western.png
```

### 5. Run Examples

```bash
python examples/generate_examples.py
```

## 🗺️ Visualization Examples

### Texas Transmission Network
![Texas Example](outputs/texas_transmission.png)

### Capacity Classes
The visualization system uses 6 capacity classes for clear visual distinction:

- **< 200 MW**: Thin lines (local distribution)
- **200-500 MW**: Light lines (sub-transmission) 
- **500-1K MW**: Medium lines (transmission)
- **1K-2K MW**: Thick lines (high voltage)
- **2K-5K MW**: Very thick lines (extra high voltage)
- **5K+ MW**: Thickest lines (ultra high voltage corridors)

## 📁 Project Structure

```
transmission-network-analysis/
├── src/                          # Core source code
│   ├── run_transmission.py       # Main aggregation script
│   ├── visualize_transmission.py # Visualization engine
│   └── grid2county_txcap.py     # Aggregation functions
├── examples/                     # Example scripts and outputs
│   ├── generate_examples.py     # Create sample visualizations
│   └── README.md                # Examples documentation
├── data/                        # Input data
│   ├── base_grid/              # MATPOWER grid data
│   └── counties/               # US county shapefiles
├── outputs/                     # Generated results
│   ├── county_edges_tx.csv     # Main output dataset
│   └── README.md               # Output documentation
├── tests/                       # Unit tests
├── docs/                        # Documentation
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🔍 Data Schema

The output `county_edges_tx.csv` contains 21 columns:

### Geographic Information
- `from_fips`, `to_fips`: County FIPS codes
- `from_county`, `to_county`: County names
- `from_state`, `to_state`: State abbreviations
- `from_lat`, `from_lon`, `to_lat`, `to_lon`: Coordinates

### Network Information  
- `from_zone_id`, `to_zone_id`: Zone identifiers
- `from_zone_name`, `to_zone_name`: Zone names
- `from_interconnect`, `to_interconnect`: Interconnect regions

### Transmission Details
- `total_capacity_mw`: Combined transmission capacity
- `edge_type`: 'AC' or 'HVDC'
- `num_circuits`, `num_links`: Circuit/link counts
- `total_impedance`: Electrical characteristics

## 🎯 Use Cases

- **Grid Planning**: Identify transmission bottlenecks and expansion needs
- **Policy Analysis**: Analyze inter-regional transmission capabilities
- **Research**: Academic studies on power system topology
- **Education**: Teaching power systems geography and capacity
- **Visualization**: Create publication-quality transmission maps

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/
```

## 📖 Documentation

Detailed documentation is available in the `docs/` folder:
- [API Reference](docs/api.md)
- [Data Format Guide](docs/data_format.md)
- [Visualization Guide](docs/visualization.md)

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Original Dataset
This work uses the **USA Test System** dataset:
- **Xu, B., Dvorkin, Y., Kirschen, D. S., Silva-Monroy, C. A., & Watson, J. P. (2021).** *A Synthetic Time-Variant U.S. Power Grid Data Set for the Evaluation of Variable Generation and Demand Response*. Zenodo. https://doi.org/10.5281/zenodo.4538590

### Software & Libraries
- **MATPOWER** for the grid data format specification
- **US Census Bureau** for county boundary shapefiles
- **Python Geospatial Community** (GeoPandas, Shapely, PyProj) for spatial analysis tools
- **Visualization Libraries** (Matplotlib, Plotly) for mapping capabilities

### Research Context
The original dataset was developed to support research in:
- Variable renewable energy integration
- Demand response optimization  
- Power system planning and operations
- Grid resilience and reliability analysis
- US Census Bureau for county shapefiles
- Python geospatial community (GeoPandas, Shapely, etc.)

---

*For questions about the underlying grid dataset or methodology, please refer to the documentation or open an issue.*
