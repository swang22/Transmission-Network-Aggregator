#!/usr/bin/env python3
"""
visualize_transmission.py
-------------------------
Visualize transmission capacity within a specified region (zone, state, or interconnection).
Creates a map showing counties and transmission lines with widths proportional to capacity.

USAGE:
  python visualize_transmission.py --region "Texas" --type interconnect --output texas_transmission.png
  python visualize_transmission.py --region "California" --type state --output ca_transmission.html
  python visualize_transmission.py --region "Alabama" --type zone --output alabama_transmission.png
"""

import argparse
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import numpy as np

# Optional interactive plotting
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.offline import plot
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def load_transmission_data(csv_path: str) -> pd.DataFrame:
    """Load the transmission edges CSV."""
    return pd.read_csv(csv_path)

def load_counties_shapefile(shp_path: str) -> gpd.GeoDataFrame:
    """Load the counties shapefile."""
    return gpd.read_file(shp_path)

def filter_region_edges(edges_df: pd.DataFrame, region_name: str, region_type: str) -> pd.DataFrame:
    """
    Filter transmission edges within a specified region.
    
    Args:
        edges_df: DataFrame with transmission edges
        region_name: Name of the region to filter by
        region_type: Type of region ('zone', 'state', 'interconnect')
    
    Returns:
        Filtered DataFrame containing only edges within the region
    """
    if region_type.lower() == 'zone':
        # Filter by zone name
        mask = ((edges_df['From_zone_name'] == region_name) | 
                (edges_df['To_zone_name'] == region_name))
    elif region_type.lower() == 'state':
        # Filter by state name or abbreviation
        mask = ((edges_df['From_state'] == region_name) | 
                (edges_df['To_state'] == region_name))
    elif region_type.lower() == 'interconnect':
        # Filter by interconnect name
        mask = ((edges_df['From_interconnect'] == region_name) | 
                (edges_df['To_interconnect'] == region_name))
    else:
        raise ValueError(f"Unknown region_type: {region_type}. Use 'zone', 'state', or 'interconnect'")
    
    return edges_df[mask].copy()

def get_region_counties(counties_gdf: gpd.GeoDataFrame, edges_df: pd.DataFrame, region_name: str, region_type: str) -> gpd.GeoDataFrame:
    """Get counties that appear in the filtered transmission edges and match the region."""
    # Convert FIPS codes to proper 5-digit strings with leading zeros
    fips_list = set()
    for fips in edges_df['From_fips'].tolist() + edges_df['To_fips'].tolist():
        fips_str = str(fips).zfill(5)
        fips_list.add(fips_str)
    
    region_counties = counties_gdf[counties_gdf['GEOID'].isin(fips_list)].copy()
    
    # Additional filtering based on region type to ensure we only get counties in the region
    if region_type.lower() == 'state':
        # Get state FIPS codes that match the region name (handle both full name and abbreviation)
        state_fips_in_region = set()
        for _, edge in edges_df.iterrows():
            if edge['From_state'] == region_name or edge['To_state'] == region_name:
                from_state_fips = str(edge['From_fips']).zfill(5)[:2]  # First 2 digits are state FIPS
                to_state_fips = str(edge['To_fips']).zfill(5)[:2]
                state_fips_in_region.add(from_state_fips)
                state_fips_in_region.add(to_state_fips)
        
        # Filter counties by state FIPS
        if state_fips_in_region:
            region_counties = region_counties[region_counties['GEOID'].str[:2].isin(state_fips_in_region)]
    
    return region_counties

def create_transmission_lines_gdf(edges_df: pd.DataFrame, counties_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Create a GeoDataFrame with transmission lines as LineString geometries.
    Lines connect county centroids.
    """
    from shapely.geometry import LineString
    
    if counties_gdf.empty or edges_df.empty:
        # Return empty GeoDataFrame with proper structure
        return gpd.GeoDataFrame(columns=['geometry', 'From_fips', 'To_fips', 'From_County', 
                                        'To_County', 'Tx_Capacity_MW', 'edge_type', 
                                        'n_circuits', 'n_links'], 
                               crs=counties_gdf.crs if not counties_gdf.empty else 'EPSG:4326')
    
    # Project to a suitable CRS for centroid calculation
    counties_projected = counties_gdf.to_crs('EPSG:3857')  # Web Mercator
    
    # Calculate county centroids
    counties_centroids = counties_projected.copy()
    counties_centroids['centroid'] = counties_centroids.geometry.centroid
    
    # Transform centroids back to original CRS
    centroids_original = counties_centroids.set_geometry('centroid').to_crs(counties_gdf.crs)
    centroids_dict = dict(zip(centroids_original['GEOID'], centroids_original['centroid']))
    
    # Create transmission lines
    lines = []
    for _, edge in edges_df.iterrows():
        from_fips = str(edge['From_fips']).zfill(5)  # Convert to 5-digit string
        to_fips = str(edge['To_fips']).zfill(5)      # Convert to 5-digit string
        
        if from_fips in centroids_dict and to_fips in centroids_dict:
            line_geom = LineString([centroids_dict[from_fips], centroids_dict[to_fips]])
            lines.append({
                'geometry': line_geom,
                'From_fips': from_fips,
                'To_fips': to_fips,
                'From_County': edge['From_County'],
                'To_County': edge['To_County'],
                'Tx_Capacity_MW': edge['Tx_Capacity_MW'],
                'edge_type': edge['edge_type'],
                'n_circuits': edge.get('n_circuits', 1),
                'n_links': edge.get('n_links', np.nan)
            })
    
    if not lines:
        # Return empty GeoDataFrame with proper structure
        return gpd.GeoDataFrame(columns=['geometry', 'From_fips', 'To_fips', 'From_County', 
                                        'To_County', 'Tx_Capacity_MW', 'edge_type', 
                                        'n_circuits', 'n_links'], 
                               crs=counties_gdf.crs)
    
    return gpd.GeoDataFrame(lines, crs=counties_gdf.crs)

def get_capacity_class_info(capacity: float) -> tuple:
    """
    Get capacity class information including width, color intensity, and label.
    Returns (width, alpha, label)
    """
    if capacity < 200:
        return 0.8, 0.4, '<200 MW'
    elif capacity < 500:
        return 1.5, 0.5, '200-500 MW'
    elif capacity < 1000:
        return 2.5, 0.6, '500-1K MW'
    elif capacity < 2000:
        return 4.0, 0.7, '1K-2K MW'
    elif capacity < 5000:
        return 6.0, 0.8, '2K-5K MW'
    else:
        return 8.0, 1.0, '5K+ MW'

def get_capacity_classes() -> list:
    """Get all capacity classes for legend."""
    return [
        ('<200 MW', 0.8, 0.4),
        ('200-500 MW', 1.5, 0.5),
        ('500-1K MW', 2.5, 0.6),
        ('1K-2K MW', 4.0, 0.7),
        ('2K-5K MW', 6.0, 0.8),
        ('5K+ MW', 8.0, 1.0)
    ]

def plot_transmission_map_matplotlib(counties_gdf: gpd.GeoDataFrame, 
                                   transmission_gdf: gpd.GeoDataFrame,
                                   region_name: str,
                                   region_type: str,
                                   output_path: str = None,
                                   figsize: tuple = (15, 10)):
    """Create transmission map using matplotlib with capacity-based line classes."""
    
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    
    # Plot counties
    counties_gdf.plot(ax=ax, color='lightgray', edgecolor='white', linewidth=0.5, alpha=0.7)
    
    if transmission_gdf.empty:
        ax.set_title(f'No transmission data for {region_name} ({region_type.title()})', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Map saved to: {output_path}")
        else:
            plt.show()
        return fig, ax
    
    # Get capacity classes for legend tracking
    capacity_classes = get_capacity_classes()
    plotted_classes = set()
    
    # Plot transmission lines by capacity class
    for _, line in transmission_gdf.iterrows():
        capacity = line['Tx_Capacity_MW']
        width, alpha, class_label = get_capacity_class_info(capacity)
        
        # Color by edge type
        if line['edge_type'] == 'AC':
            color = 'blue'
            line_style = '-'
        else:  # HVDC
            color = 'red'
            line_style = '-'
        
        # Plot individual line
        gpd.GeoSeries([line['geometry']]).plot(
            ax=ax, color=color, linewidth=width, alpha=alpha, linestyle=line_style
        )
        
        plotted_classes.add((class_label, width, color, line['edge_type'], alpha))
    
    # Styling
    ax.set_title(f'Transmission Network - {region_name} ({region_type.title()})', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True, alpha=0.3)
    
    # Create legend
    legend_elements = []
    
    # Add edge type legend
    has_ac = any(line['edge_type'] == 'AC' for _, line in transmission_gdf.iterrows())
    has_hvdc = any(line['edge_type'] == 'HVDC' for _, line in transmission_gdf.iterrows())
    
    if has_ac:
        legend_elements.append(mpatches.Patch(color='blue', alpha=0.7, label='AC Lines'))
    if has_hvdc:
        legend_elements.append(mpatches.Patch(color='red', alpha=0.8, label='HVDC Lines'))
    
    # Add spacing
    if legend_elements:
        legend_elements.append(mpatches.Patch(color='none', label=''))
    
    # Add capacity classes
    legend_elements.append(mpatches.Patch(color='none', label='Capacity Classes:'))
    
    # Get unique capacity classes that were actually plotted
    plotted_capacity_classes = set()
    for _, line in transmission_gdf.iterrows():
        _, _, class_label = get_capacity_class_info(line['Tx_Capacity_MW'])
        plotted_capacity_classes.add(class_label)
    
    # Add capacity class legend entries in order
    for class_label, width, alpha in capacity_classes:
        if class_label in plotted_capacity_classes:
            # Create a line patch to show width
            legend_elements.append(
                plt.Line2D([0], [0], color='gray', linewidth=width, alpha=alpha, label=class_label)
            )
    
    if legend_elements:
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Map saved to: {output_path}")
    else:
        plt.show()
    
    return fig, ax

def plot_transmission_map_plotly(counties_gdf: gpd.GeoDataFrame,
                               transmission_gdf: gpd.GeoDataFrame,
                               region_name: str,
                               region_type: str,
                               output_path: str = None):
    """Create interactive transmission map using plotly with capacity classes."""
    
    if not PLOTLY_AVAILABLE:
        raise ImportError("Plotly not available. Install with: pip install plotly")
    
    fig = go.Figure()
    
    # Add counties
    for _, county in counties_gdf.iterrows():
        # Convert to lat/lon coordinates for plotly
        if hasattr(county.geometry, 'exterior'):
            # Polygon
            coords = list(county.geometry.exterior.coords)
        else:
            # MultiPolygon - take the largest polygon
            coords = list(max(county.geometry.geoms, key=lambda x: x.area).exterior.coords)
        
        lons, lats = zip(*coords)
        
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            fill='toself',
            fillcolor='rgba(200, 200, 200, 0.3)',
            line=dict(color='white', width=1),
            name='County',
            showlegend=False,
            hovertemplate=f"<b>{county.get('NAME', 'County')}</b><extra></extra>"
        ))
    
    # Track capacity classes for legend
    capacity_class_traces = {}
    
    # Add transmission lines by capacity class
    for _, line in transmission_gdf.iterrows():
        coords = list(line.geometry.coords)
        lons, lats = zip(*coords)
        
        capacity = line['Tx_Capacity_MW']
        width, alpha, class_label = get_capacity_class_info(capacity)
        
        # Color by edge type
        if line['edge_type'] == 'AC':
            color = f'rgba(0, 0, 255, {alpha})'  # Blue with alpha
            line_name = f'AC - {class_label}'
        else:  # HVDC
            color = f'rgba(255, 0, 0, {alpha})'  # Red with alpha
            line_name = f'HVDC - {class_label}'
        
        # Create trace key for legend grouping
        trace_key = (line['edge_type'], class_label)
        trace_key_str = f"{line['edge_type']}_{class_label.replace(' ', '_').replace('-', '_')}"
        
        if trace_key not in capacity_class_traces:
            # First line of this class - show in legend
            show_legend = True
            capacity_class_traces[trace_key] = True
        else:
            show_legend = False
        
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            line=dict(color=color, width=width),
            name=line_name,
            showlegend=show_legend,
            legendgroup=trace_key_str,
            hovertemplate=f"<b>{line['From_County']} ↔ {line['To_County']}</b><br>" +
                         f"Type: {line['edge_type']}<br>" +
                         f"Capacity: {line['Tx_Capacity_MW']:.0f} MW<br>" +
                         f"Class: {class_label}<br>" +
                         f"<extra></extra>"
        ))
    
    # Set mapbox style and center
    if not counties_gdf.empty:
        center_lat = counties_gdf.geometry.centroid.y.mean()
        center_lon = counties_gdf.geometry.centroid.x.mean()
    else:
        center_lat, center_lon = 39.8, -98.5  # Center of US
    
    fig.update_layout(
        title=f'Interactive Transmission Network - {region_name} ({region_type.title()})<br>' +
              '<sub>Line width indicates capacity class, hover for details</sub>',
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=6
        ),
        showlegend=True,
        height=700,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01,
            title="Transmission Lines"
        )
    )
    
    if output_path:
        if output_path.endswith('.html'):
            plot(fig, filename=output_path, auto_open=False)
            print(f"Interactive map saved to: {output_path}")
        else:
            fig.write_image(output_path)
            print(f"Map saved to: {output_path}")
    else:
        fig.show()
    
    return fig

def main():
    parser = argparse.ArgumentParser(description="Visualize transmission network for a region")
    parser.add_argument("--region", required=True, help="Region name (e.g., 'Texas', 'California', 'Alabama')")
    parser.add_argument("--type", required=True, choices=['zone', 'state', 'interconnect'], 
                       help="Type of region")
    parser.add_argument("--edges-file", default="../outputs/county_edges_tx.csv", 
                       help="Path to transmission edges CSV file")
    parser.add_argument("--counties-file", default="../data/counties/cb_2022_us_county_500k.shp",
                       help="Path to counties shapefile")
    parser.add_argument("--output", help="Output file path (.png, .jpg, .svg, .html)")
    parser.add_argument("--interactive", action="store_true", 
                       help="Create interactive plot (requires plotly)")
    parser.add_argument("--figsize", nargs=2, type=float, default=[15, 10],
                       help="Figure size (width height) for static plots")
    
    args = parser.parse_args()
    
    # Resolve paths relative to the script location
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    # Fix paths if they're relative
    if not Path(args.edges_file).is_absolute():
        if args.edges_file.startswith("../"):
            args.edges_file = str(repo_root / args.edges_file[3:])
        else:
            args.edges_file = str(script_dir / args.edges_file)
    
    if not Path(args.counties_file).is_absolute():
        if args.counties_file.startswith("../"):
            args.counties_file = str(repo_root / args.counties_file[3:])
        else:
            args.counties_file = str(script_dir / args.counties_file)
    
    # Load data
    print(f"Loading transmission edges from: {args.edges_file}")
    edges_df = load_transmission_data(args.edges_file)
    
    print(f"Loading counties shapefile from: {args.counties_file}")
    counties_gdf = load_counties_shapefile(args.counties_file)
    
    # Filter edges for the specified region
    print(f"Filtering transmission edges for {args.region} ({args.type})")
    region_edges = filter_region_edges(edges_df, args.region, args.type)
    
    if region_edges.empty:
        print(f"No transmission edges found for region '{args.region}' of type '{args.type}'")
        print(f"Available {args.type}s:", 
              edges_df[f'From_{args.type}' if args.type != 'state' else 'From_state'].dropna().unique())
        return
    
    print(f"Found {len(region_edges)} transmission edges in the region")
    
    # Get counties in the region
    region_counties = get_region_counties(counties_gdf, region_edges, args.region, args.type)
    print(f"Region contains {len(region_counties)} counties")
    
    # Create transmission lines geodataframe
    transmission_gdf = create_transmission_lines_gdf(region_edges, region_counties)
    print(f"Created {len(transmission_gdf)} transmission line geometries")
    
    # Create visualization
    if args.interactive and PLOTLY_AVAILABLE:
        plot_transmission_map_plotly(region_counties, transmission_gdf, 
                                   args.region, args.type, args.output)
    else:
        if args.interactive and not PLOTLY_AVAILABLE:
            print("Plotly not available. Creating static plot instead.")
        plot_transmission_map_matplotlib(region_counties, transmission_gdf,
                                       args.region, args.type, args.output, 
                                       figsize=tuple(args.figsize))

if __name__ == "__main__":
    main()
