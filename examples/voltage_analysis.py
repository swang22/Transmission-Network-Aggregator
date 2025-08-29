#!/usr/bin/env python3
"""
Analyze voltage levels in the transmission dataset to inform filtering decisions.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

def analyze_voltage_levels():
    """Analyze voltage level distribution in the dataset"""
    
    print("🔍 VOLTAGE LEVEL ANALYSIS")
    print("=" * 50)
    
    # Load data directly
    GRID_DIR = Path("data") / "base_grid"
    bus = pd.read_csv(GRID_DIR / "bus.csv")
    branch = pd.read_csv(GRID_DIR / "branch.csv")
    
    # Check voltage data availability
    voltage_cols = [col for col in bus.columns if any(v in col.lower() for v in ['voltage', 'kv'])]
    print(f"Bus voltage columns found: {voltage_cols}")
    
    # Use the correct voltage column (baseKV with capital letters)
    voltage_col = None
    for col in ['baseKV', 'basekv', 'base_kv', 'voltage_kv']:
        if col in bus.columns:
            voltage_col = col
            break
    
    if voltage_col is None:
        print("❌ No voltage columns found in dataset!")
        return
        
    print(f"Using voltage column: '{voltage_col}'")
    
    # Analyze bus voltage levels
    print(f"\n📊 BUS VOLTAGE LEVEL DISTRIBUTION")
    print("-" * 30)
    
    voltage_counts = bus[voltage_col].value_counts().sort_index()
    print(f"Total buses: {len(bus):,}")
    print("Voltage distribution:")
    
    transmission_total = 0
    distribution_total = 0
    
    for kv, count in voltage_counts.items():
        pct = count / len(bus) * 100
        category = "TRANSMISSION" if kv >= 138 else "DISTRIBUTION" 
        if kv >= 138:
            transmission_total += count
        else:
            distribution_total += count
        print(f"  {kv:>6.0f} kV: {count:>8,} buses ({pct:>5.1f}%) - {category}")
    
    print(f"\n📈 SUMMARY:")
    print(f"  Transmission (≥138 kV): {transmission_total:,} buses ({transmission_total/len(bus)*100:.1f}%)")
    print(f"  Distribution (<138 kV):  {distribution_total:,} buses ({distribution_total/len(bus)*100:.1f}%)")
    
    # Common voltage thresholds
    thresholds = [69, 115, 138, 230, 345, 500, 765]
    print(f"\n⚡ BUSES BY VOLTAGE THRESHOLD:")
    for threshold in thresholds:
        above_threshold = (bus[voltage_col] >= threshold).sum()
        pct = above_threshold / len(bus) * 100
        print(f"  ≥{threshold:>3} kV: {above_threshold:>8,} buses ({pct:>5.1f}%)")
    
    # Branch analysis
    print(f"\n📊 BRANCH IMPACT ANALYSIS")
    print("-" * 30)
    
    # Check branch rating column
    rate_cols = [col for col in branch.columns if 'rate' in col.lower()]
    print(f"Branch rating columns: {rate_cols}")
    
    rate_col = None
    for col in ['rateA', 'ratea', 'rate_a', 'rate']:
        if col in branch.columns:
            rate_col = col
            break
    
    if rate_col is not None:
        print(f"Using rating column: '{rate_col}'")
        
        # Merge voltage from buses to branches
        bus_voltage = bus[['bus_id', voltage_col]]
        branch_with_voltage = branch.merge(bus_voltage, left_on='from_bus_id', right_on='bus_id', how='left')
        
        voltage_capacity = branch_with_voltage.groupby(voltage_col)[rate_col].agg(['count', 'sum']).sort_index()
        voltage_capacity.columns = ['branch_count', 'total_capacity_mw']
        
        print(f"\nTotal branches: {len(branch):,}")
        print("Branch capacity by voltage level:")
        
        trans_branches = 0
        dist_branches = 0  
        trans_capacity = 0
        dist_capacity = 0
        
        for kv, row in voltage_capacity.iterrows():
            if not pd.isna(kv):
                category = "TRANSMISSION" if kv >= 138 else "DISTRIBUTION"
                if kv >= 138:
                    trans_branches += row['branch_count']
                    trans_capacity += row['total_capacity_mw']
                else:
                    dist_branches += row['branch_count'] 
                    dist_capacity += row['total_capacity_mw']
                print(f"  {kv:>6.0f} kV: {row['branch_count']:>6,} branches, {row['total_capacity_mw']:>10,.0f} MW - {category}")
        
        total_capacity = trans_capacity + dist_capacity
        total_branches = trans_branches + dist_branches
        
        print(f"\n⚡ TRANSMISSION-ONLY FILTERING IMPACT (≥138 kV):")
        print(f"  Would keep: {trans_branches:,}/{total_branches:,} branches ({trans_branches/total_branches*100:.1f}%)")
        print(f"  Would keep: {trans_capacity:,.0f}/{total_capacity:,.0f} MW capacity ({trans_capacity/total_capacity*100:.1f}%)")
        print(f"  Would remove: {dist_branches:,} distribution branches ({dist_capacity:,.0f} MW)")
        
        # Show impact of other thresholds
        print(f"\n📊 IMPACT OF DIFFERENT VOLTAGE THRESHOLDS:")
        for threshold in [115, 138, 230, 345]:
            threshold_data = voltage_capacity[voltage_capacity.index >= threshold]
            if len(threshold_data) > 0:
                thresh_branches = threshold_data['branch_count'].sum()
                thresh_capacity = threshold_data['total_capacity_mw'].sum()
                print(f"  ≥{threshold:>3} kV: {thresh_branches:>6,} branches ({thresh_branches/total_branches*100:>5.1f}%), {thresh_capacity:>10,.0f} MW ({thresh_capacity/total_capacity*100:>5.1f}%)")

def create_voltage_visualization():
    """Create voltage level visualization"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not available for visualization")
        return
        
    # Load data
    GRID_DIR = Path("data") / "base_grid"
    bus = pd.read_csv(GRID_DIR / "bus.csv")
    
    # Find voltage column
    voltage_col = None
    for col in ['baseKV', 'basekv', 'base_kv', 'voltage_kv']:
        if col in bus.columns:
            voltage_col = col
            break
    
    if voltage_col is None:
        print("No voltage data available for visualization")
        return
    
    # Create voltage distribution plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Histogram
    voltage_data = bus[voltage_col].dropna()
    ax1.hist(voltage_data, bins=50, alpha=0.7, edgecolor='black')
    ax1.axvline(138, color='red', linestyle='--', linewidth=2, label='Transmission Threshold (138 kV)')
    ax1.set_xlabel('Voltage Level (kV)')
    ax1.set_ylabel('Number of Buses')
    ax1.set_title('Voltage Level Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Bar chart of major voltage levels
    voltage_counts = voltage_data.value_counts().sort_index()
    major_voltages = voltage_counts[voltage_counts >= 50]  # Only show levels with 50+ buses
    
    colors = ['red' if v < 138 else 'blue' for v in major_voltages.index]
    ax2.bar(range(len(major_voltages)), major_voltages.values, color=colors, alpha=0.7)
    ax2.set_xticks(range(len(major_voltages)))
    ax2.set_xticklabels([f'{v:.0f}' for v in major_voltages.index], rotation=45)
    ax2.set_xlabel('Voltage Level (kV)')
    ax2.set_ylabel('Number of Buses')
    ax2.set_title('Major Voltage Levels (≥50 buses)')
    ax2.grid(True, alpha=0.3)
    
    # Add legend
    import matplotlib.patches as mpatches
    red_patch = mpatches.Patch(color='red', alpha=0.7, label='Distribution (<138 kV)')
    blue_patch = mpatches.Patch(color='blue', alpha=0.7, label='Transmission (≥138 kV)')
    ax2.legend(handles=[red_patch, blue_patch])
    
    plt.tight_layout()
    output_path = Path("outputs") / "voltage_analysis.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n📊 Voltage analysis plot saved to: {output_path}")

def recommend_filtering():
    """Provide filtering recommendations based on data analysis"""
    print(f"\n💡 FILTERING RECOMMENDATIONS")
    print("=" * 50)
    print("Based on the analysis above:")
    print("")
    print("🔹 For TRANSMISSION ANALYSIS:")
    print("   python src/run_transmission.py --transmission-only")
    print("   (Uses ≥138 kV threshold - standard transmission definition)")
    print("")
    print("🔹 For HIGH-VOLTAGE TRANSMISSION only:")
    print("   python src/run_transmission.py --min-voltage 230")
    print("   (Excludes sub-transmission 115-138 kV lines)")
    print("")
    print("🔹 For SPECIFIC VOLTAGE LEVELS:")
    print("   python src/run_transmission.py --voltage-levels 345 500 765")
    print("   (Only includes extra-high voltage lines)")
    print("")
    print("🔹 For COMPARISON:")
    print("   # All voltages")
    print("   python src/run_transmission.py --output outputs/all_voltages.csv")
    print("   # Transmission only")
    print("   python src/run_transmission.py --transmission-only --output outputs/transmission_only.csv")
    print("")
    print("📈 The voltage filtering helps by:")
    print("   • Preventing capacity inflation from distribution lines")
    print("   • Focusing on bulk power transfer capability")  
    print("   • Following standard power system definitions")
    print("   • Eliminating local distribution interconnections")

if __name__ == "__main__":
    try:
        analyze_voltage_levels()
        create_voltage_visualization()
        recommend_filtering()
    except Exception as e:
        print(f"Error in voltage analysis: {e}")
        import traceback
        traceback.print_exc()
