# Output Files

This folder contains generated results from the transmission analysis.

## Main Output

### `county_edges_tx.csv`
The primary output file containing 7,652 transmission edges with 21 columns:

#### Geographic Information
- `from_fips`, `to_fips`: County FIPS codes (5-digit)
- `from_county`, `to_county`: County names
- `from_state`, `to_state`: State abbreviations  
- `from_lat`, `from_lon`, `to_lat`, `to_lon`: Geographic coordinates

#### Network Topology
- `from_zone_id`, `to_zone_id`: Zone identifiers
- `from_zone_name`, `to_zone_name`: Zone names (e.g., "Alabama", "California")
- `from_interconnect`, `to_interconnect`: Interconnect regions ("Eastern", "Western", "Texas")

#### Transmission Characteristics
- `total_capacity_mw`: Aggregated transmission capacity (MW)
- `edge_type`: Line type ("AC" or "HVDC")
- `num_circuits`, `num_links`: Number of parallel circuits/links
- `total_impedance`: Aggregated electrical impedance
- Additional technical parameters

## Visualizations

Generated maps and interactive visualizations:
- `*.png`: Static transmission maps (matplotlib)
- `*.html`: Interactive transmission maps (plotly)
- `*.jpg`, `*.svg`: Alternative static formats

## Data Statistics

- **Total Edges**: 7,652
- **AC Lines**: 7,637 (99.8%)
- **HVDC Lines**: 15 (0.2%)
- **Capacity Range**: 0 - 31,600 MW
- **Geographic Coverage**: Continental United States
- **Interconnects**: Eastern (3,456 edges), Western (2,890 edges), Texas (1,306 edges)

## Usage

The CSV file can be used with:
- Pandas for data analysis
- GeoPandas for geospatial analysis
- GIS software (QGIS, ArcGIS) for mapping
- Network analysis tools (NetworkX, igraph)
- Power system analysis software

## File Format

Standard CSV format with UTF-8 encoding. Geographic coordinates are in WGS84 (EPSG:4326).

Load with pandas:
```python
import pandas as pd
edges = pd.read_csv('county_edges_tx.csv')
```
