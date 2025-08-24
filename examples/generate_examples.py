#!/usr/bin/env python3
"""
generate_examples.py
--------------------
Example script demonstrating different transmission visualizations with capacity classes.

This script creates several example maps showing different regions and the new
capacity-based line visualization features.
"""

import subprocess
import sys
from pathlib import Path

def run_visualization(region, region_type, output_file, interactive=False, figsize=None):
    """Run a transmission visualization."""
    # Path to visualization script in src folder
    script_path = Path(__file__).parent.parent / "src" / "visualize_transmission.py"
    
    cmd = [
        sys.executable, str(script_path),
        "--region", region,
        "--type", region_type,
        "--output", output_file
    ]
    
    if interactive:
        cmd.append("--interactive")
    
    if figsize:
        cmd.extend(["--figsize"] + [str(x) for x in figsize])
    
    print(f"Creating visualization: {region} ({region_type}) -> {output_file}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Success: {output_file}")
        else:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Exception: {e}")

def main():
    """Create example visualizations."""
    
    # Check if required files exist
    repo_root = Path(__file__).parent.parent
    county_edges_path = repo_root / "outputs" / "county_edges_tx.csv"
    counties_path = repo_root / "data" / "counties" / "cb_2022_us_county_500k.shp"
    
    if not county_edges_path.exists():
        print("Error: county_edges_tx.csv not found. Run src/run_transmission.py first.")
        return
    
    if not counties_path.exists():
        print("Error: Counties shapefile not found.")
        return
    
    print("Creating example transmission visualizations...")
    print("=" * 50)
    
    # 1. Texas State - Static Map
    run_visualization("TX", "state", "examples/texas_transmission.png", figsize=[15, 10])
    
    # 2. California State - Interactive Map
    run_visualization("CA", "state", "examples/california_interactive.html", interactive=True)
    
    # 3. Alabama Zone - Static Map
    run_visualization("Alabama", "zone", "examples/alabama_zone.png")
    
    # 4. Western Interconnect - Large Static Map
    run_visualization("Western", "interconnect", "examples/western_interconnect.png", figsize=[20, 15])
    
    # 5. Eastern Interconnect - Interactive Map
    run_visualization("Eastern", "interconnect", "examples/eastern_interactive.html", interactive=True)
    
    print("\n" + "=" * 50)
    print("Example visualizations complete!")
    print("Check the 'examples/' folder for output files.")
    
    print("\n" + "=" * 50)
    print("CAPACITY CLASSES USED IN VISUALIZATIONS:")
    print("• <200 MW    - Thin lines (0.8 width, 0.4 alpha)")
    print("• 200-500 MW - Light lines (1.5 width, 0.5 alpha)")  
    print("• 500-1K MW  - Medium lines (2.5 width, 0.6 alpha)")
    print("• 1K-2K MW   - Thick lines (4.0 width, 0.7 alpha)")
    print("• 2K-5K MW   - Very thick lines (6.0 width, 0.8 alpha)")
    print("• 5K+ MW     - Thickest lines (8.0 width, 1.0 alpha)")
    print("\nLINE COLORS:")
    print("• Blue: AC transmission lines")
    print("• Red:  HVDC transmission lines")
    print("\nData includes:")
    print("• From/To counties with FIPS codes")
    print("• Zone names and interconnect information")
    print("• Total transmission capacity (MW)")
    print("• Geographic coordinates for mapping")
    print("• All 7,652 transmission edges (7,637 AC + 15 HVDC)")

if __name__ == "__main__":
    # Create examples directory
    Path("examples").mkdir(exist_ok=True)
    main()
