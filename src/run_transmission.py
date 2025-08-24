# run_transmission.py — Main script to aggregate transmission data
from pathlib import Path
import pandas as pd
import sys

# --- make sure Python can import grid2county_txcap from this folder
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent  # Go up one level to repo root
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from grid2county_txcap import (
    load_grid_tables, load_counties, build_bus_lookup,
    aggregate_ac, aggregate_hvdc
)

# --- paths
GRID_DIR = REPO_ROOT / "data" / "base_grid"    # where bus/branch/sub/bus2sub live
OUTPUT   = REPO_ROOT / "outputs" / "county_edges_tx.csv" # output location

# --- options
COUNTIES_FILE = None   # keep None to auto-fetch via pygris; or set to a local counties file path
COUNTIES_YEAR = 2022
# Insert local fallback logic
LOCAL_DIR = REPO_ROOT / "data" / "counties"
LOCAL_SHP = LOCAL_DIR / f"cb_{COUNTIES_YEAR}_us_county_500k.shp"
if LOCAL_SHP.exists():
    COUNTIES_FILE = str(LOCAL_SHP)
    print("Using local counties shapefile:", COUNTIES_FILE)
RATE = "A"             # "A" | "B" | "C"
PF_RULE = "none"       # "none" | "const:0.97" | "bykv"
INCLUDE_TRANSFORMERS = False
KEEP_INTRACOUNTY     = False
NO_HVDC              = False

# --- quick sanity check on the data folder
print("GRID_DIR:", GRID_DIR)
print("bus.*    ->", [p.name for p in GRID_DIR.glob("bus.*")])
print("branch.* ->", [p.name for p in GRID_DIR.glob("branch.*")])
print("sub.*    ->", [p.name for p in GRID_DIR.glob("sub.*")])
print("bus2sub.*->", [p.name for p in GRID_DIR.glob("bus2sub.*")])

# --- run aggregation
bus, branch, sub, bus2sub, zone, dcline = load_grid_tables(str(GRID_DIR))
counties = load_counties(COUNTIES_FILE, COUNTIES_YEAR)
bus_to_fips, bus_local = build_bus_lookup(bus, bus2sub, sub, counties, zone)

ac = aggregate_ac(
    branch=branch,
    bus_local=bus_local,
    rate_pref=RATE,
    pf_mode=PF_RULE,
    exclude_transformers=(not INCLUDE_TRANSFORMERS),
    keep_intracounty=KEEP_INTRACOUNTY,
)

if (not NO_HVDC) and (dcline is not None):
    dc = aggregate_hvdc(dcline, bus_local, keep_intracounty=KEEP_INTRACOUNTY)
    edges = pd.concat([ac, dc], ignore_index=True, sort=False) if (dc is not None and len(dc)) else ac
else:
    edges = ac

edges.to_csv(OUTPUT, index=False)
print(f"Wrote {len(edges):,} edges to {OUTPUT}")
print(edges.head())


