#!/usr/bin/env python3
"""
quick_start.py
--------------
Quick start sc    # Show basic statistics
    print(f"\n📊 DATA SUMMARY")
    print("-" * 30)
    try:
        import pandas as pd
        df = pd.read_csv(output_file)
        print(f"Total transmission edges: {len(df):,}")
        print(f"AC lines: {(df['edge_type'] == 'AC').sum():,}")
        print(f"HVDC lines: {(df['edge_type'] == 'HVDC').sum():,}")
        print(f"Capacity range: {df['Tx_Capacity_MW'].min():.0f} - {df['Tx_Capacity_MW'].max():.0f} MW")
        print(f"States covered: {df['From_state'].nunique()}")
        print(f"Counties covered: {df[['From_fips', 'To_fips']].stack().nunique()}")
    except ImportError:
        print("Install pandas to see data summary")(f"Total transmission edges: {len(df):,}")
        print(f"AC lines: {(df['edge_type'] == 'AC').sum():,}")
        print(f"HVDC lines: {(df['edge_type'] == 'HVDC').sum():,}")
        print(f"Capacity range: {df['Tx_Capacity_MW'].min():.0f} - {df['Tx_Capacity_MW'].max():.0f} MW")
        print(f"States covered: {df['From_state'].nunique()}")
        print(f"Counties covered: {df[['From_fips', 'To_fips']].stack().nunique()}") demonstrate the transmission analysis workflow.

This script runs the complete analysis pipeline:
1. Aggregates transmission data from grid files
2. Creates sample visualizations
3. Shows basic data analysis
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print status."""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")
    
    try:
        # Handle both string and list commands
        if isinstance(cmd, list):
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print("Output:", result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print("Error:", e.stderr.strip())
        return False

def main():
    """Run the quick start workflow."""
    print("🚀 TRANSMISSION NETWORK ANALYSIS - QUICK START")
    print("=" * 60)
    
    repo_root = Path(__file__).parent
    
    # Check if required data exists
    grid_dir = repo_root / "data" / "base_grid"
    if not grid_dir.exists():
        print("❌ Error: Grid data not found at", grid_dir)
        print("   Please ensure MATPOWER grid files are in data/base_grid/")
        return False
    
    required_files = ["bus.csv", "branch.csv", "sub.csv", "bus2sub.csv"]
    missing_files = [f for f in required_files if not (grid_dir / f).exists()]
    if missing_files:
        print(f"❌ Error: Missing required files: {missing_files}")
        return False
    
    print("✅ Grid data files found")
    
    # Step 1: Generate transmission aggregation
    print(f"\n📊 STEP 1: Generate transmission data")
    print("-" * 50)
    step1_cmd = [sys.executable, str(repo_root / "src" / "run_transmission.py")]
    if not run_command(step1_cmd, "Aggregating transmission data"):
        return False
    print(f"\n📊 STEP 1B: Compare with 'first' strategy")
    print("-" * 50)
    compare_script = repo_root / "examples" / "compare_multi_sub_strategies.py"
    if compare_script.exists():
        step1b_cmd = [sys.executable, str(compare_script)]
        run_command(step1b_cmd, "Comparing multi-substation strategies")
    
    # Check if output was created
    output_file = repo_root / "outputs" / "county_edges_tx.csv"
    if not output_file.exists():
        print("❌ Error: Output file not created")
        return False
    
    # Show basic statistics
    print(f"\n📊 DATA SUMMARY")
    print("-" * 30)
    try:
        import pandas as pd
        df = pd.read_csv(output_file)
        print(f"Total transmission edges: {len(df):,}")
        print(f"AC lines: {(df['edge_type'] == 'AC').sum():,}")
        print(f"HVDC lines: {(df['edge_type'] == 'HVDC').sum():,}")
        print(f"Capacity range: {df['Tx_Capacity_MW'].min():.0f} - {df['Tx_Capacity_MW'].max():.0f} MW")
        print(f"States covered: {df['From_state'].nunique()}")
        print(f"Counties covered: {df[['From_fips', 'To_fips']].stack().nunique()}")
        print(f"Multi-substation strategy: largest (default)")
    except ImportError:
        print("Install pandas to see data summary")
    
    # Step 2: Create sample visualizations
    examples_script = repo_root / "examples" / "generate_examples.py"
    if examples_script.exists():
        step2_cmd = [sys.executable, str(examples_script)]
        if run_command(step2_cmd, "Creating sample visualizations"):
            print("📊 Sample maps created in outputs/ folder")
    
    # Final summary
    print(f"\n🎉 QUICK START COMPLETE!")
    print("=" * 40)
    print("✅ Transmission data aggregated")
    print("✅ Sample visualizations created")
    print("\n📁 Check these folders:")
    print(f"   • outputs/county_edges_tx.csv - Main dataset")
    print(f"   • outputs/*.png - Static transmission maps")
    print(f"   • outputs/*.html - Interactive maps")
    print("\n🔧 Next steps:")
    print(f"   • Explore the data: python -c \"import pandas as pd; df=pd.read_csv('outputs/county_edges_tx.csv'); print(df.head())\"")
    print(f"   • Create custom maps: python src/visualize_transmission.py --region TX --type state --output my_map.png")
    print(f"   • Read the documentation: README.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
