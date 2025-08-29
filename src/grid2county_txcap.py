#!/usr/bin/env python3
"""
grid2county_txcap.py
--------------------
Aggregate transmission capacity from a MATPOWER-style U.S. grid dataset to county-level edges.

Outputs CSV columns:
  From_fips, To_fips, From_County, To_County, Tx_Capacity_MW,
  x_eq_pu, sum_B_pu, n_circuits, sum_rate_mva, edge_type,
  From_state, From_zone, To_state, To_zone
(and a couple of helper fields if available)

USAGE (examples)
  # simplest: treat rateA MVA as MW (DC convention), exclude transformers, drop intra-county
  python grid2county_txcap.py --grid-dir "E:/.../base_grid" --output county_edges_tx.csv

  # pf-adjust with a constant 0.97
  python grid2county_txcap.py --grid-dir "E:/.../base_grid" --pf const:0.97

  # pf by voltage class (<230:0.95, 230-345:0.97, >=500:0.99)
  python grid2county_txcap.py --grid-dir "E:/.../base_grid" --pf bykv

  # use a local counties file instead of downloading (any GeoJSON / Shapefile / GPKG with GEOID)
  python grid2county_txcap.py --grid-dir "E:/.../base_grid" --counties-file "counties.gpkg"
"""

import argparse
import os
from typing import Optional, Tuple

import numpy as np
import pandas as pd

# Optional geospatial deps (required if you don't pass a pre-joined county mapping)
try:
    import geopandas as gpd
    from shapely.geometry import Point
except Exception:
    gpd = None
    Point = None

# Force GeoPandas to use pyogrio instead of fiona (works even if fiona is broken)
try:
    import pyogrio
    from geopandas.io.file import _read_file as _gpd_read_file
    def _read_file_pyogrio(path, *args, **kwargs):
        return _gpd_read_file(path, engine="pyogrio", *args, **kwargs)
    gpd.read_file = _read_file_pyogrio
except Exception as _e:
    # Fallback: try the global option if your geopandas is new enough
    try:
        gpd.options.io_engine = "pyogrio"
    except Exception:
        pass

# Optional on-the-fly county fetch
try:
    from pygris import counties as pg_counties
except Exception:
    pg_counties = None

# Optional state code helper
try:
    import us as usmod
except Exception:
    usmod = None


# ---------- I/O helpers ----------

def read_tabular(path: str, index_col: Optional[int] = None) -> pd.DataFrame:
    """Read CSV / XLSX / XLS / Parquet with a single function."""
    p = path.lower()
    if p.endswith(".csv"):
        return pd.read_csv(path, index_col=index_col)
    if p.endswith(".xlsx") or p.endswith(".xls"):
        return pd.read_excel(path, index_col=index_col)
    if p.endswith(".parquet"):
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported table format: {path}")


def find_file(grid_dir: str, basename: str) -> Optional[str]:
    """Find a file (csv/xlsx/xls/parquet) with a common base name."""
    for ext in (".csv", ".xlsx", ".xls", ".parquet", ""):
        cand = os.path.join(grid_dir, basename + ext)
        if os.path.exists(cand):
            return cand
    return None


def load_grid_tables(grid_dir: str):
    req = ["bus", "branch", "sub", "bus2sub"]
    missing = [b for b in req if not find_file(grid_dir, b)]
    if missing:
        raise FileNotFoundError(f"Missing required files in {grid_dir}: {missing}")

    bus = read_tabular(find_file(grid_dir, "bus"))
    branch = read_tabular(find_file(grid_dir, "branch"))
    sub = read_tabular(find_file(grid_dir, "sub"))
    bus2sub = read_tabular(find_file(grid_dir, "bus2sub"))

    zone = None
    zf = find_file(grid_dir, "zone")
    if zf:
        zone = read_tabular(zf)

    dcline = None
    dcf = find_file(grid_dir, "dcline")
    if dcf:
        dcline = read_tabular(dcf)

    # normalize column names to lower case
    for df in (bus, branch, sub, bus2sub, zone, dcline):
        if df is not None:
            df.columns = [c.lower() for c in df.columns]

    return bus, branch, sub, bus2sub, zone, dcline


# ---------- Counties layer ----------

def load_counties(counties_file: Optional[str], year: int):
    """Load counties GeoDataFrame either from file or via pygris."""
    if counties_file:
        if gpd is None:
            raise RuntimeError("geopandas required to read counties file. Install geopandas/pyogrio.")
        gdf = gpd.read_file(counties_file)
        # Must have GEOID column (5-digit FIPS). If not, try to derive it.
        if "GEOID" not in gdf.columns:
            # Try to build from STATEFP + COUNTYFP if present
            if {"STATEFP", "COUNTYFP"}.issubset(set(gdf.columns)):
                gdf["GEOID"] = gdf["STATEFP"].astype(str).str.zfill(2) + gdf["COUNTYFP"].astype(str).str.zfill(3)
            else:
                raise KeyError("Counties file must contain GEOID or STATEFP+COUNTYFP.")
        # keep standard fields
        keep = ["GEOID", "STATEFP", "NAME", "geometry"]
        for k in keep:
            if k not in gdf.columns and k != "geometry":
                gdf[k] = None
        return gdf[keep].copy()

    # else: fetch with pygris
    if gpd is None or pg_counties is None:
        raise RuntimeError("To fetch counties automatically, install geopandas + pygris.")
    gdf = pg_counties(cb=True, year=year)
    keep = ["GEOID", "STATEFP", "NAME", "geometry"]
    return gdf[keep].copy()


def state_abbrev_from_fips(statefp: Optional[str]) -> str:
    if statefp is None:
        return ""
    sf = str(statefp).zfill(2)
    if usmod is None:
        return sf
    for st in usmod.states.STATES_AND_TERRITORIES:
        if getattr(st, "fips", None) == sf:
            return st.abbr
    return sf


# ---------- Core logic ----------

def mk_pf_from_kv(kv: float, rules=(0.95, 0.97, 0.99)) -> float:
    """pf by nominal voltage: <230:0.95, 230-345:0.97, >=500:0.99."""
    try:
        if kv >= 500 - 1e-6:
            return rules[2]
        if kv >= 230 - 1e-6:
            return rules[1]
        return rules[0]
    except Exception:
        return 1.0


def pick_rating(row: pd.Series, prefer: str) -> float:
    """Choose rating value from rateA/B/C, skipping zeros (MATPOWER: 0 = not specified)."""
    ladder = {
        "a": ["ratea", "rateb", "ratec"],
        "b": ["rateb", "ratea", "ratec"],
        "c": ["ratec", "rateb", "ratea"],
    }.get(prefer.lower(), ["ratea", "rateb", "ratec"])
    for col in ladder:
        if col in row and pd.notna(row[col]):
            try:
                v = float(row[col])
                if v > 0:
                    return v
            except Exception:
                pass
    return np.nan


def unordered_pair(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    arr = df[[a, b]].to_numpy().astype(object)
    swap = arr[:, 0] > arr[:, 1]
    arr[swap] = arr[swap][:, ::-1]
    return pd.DataFrame(arr, columns=["fips_lo", "fips_hi"], index=df.index)


def build_bus_lookup(bus: pd.DataFrame, bus2sub: pd.DataFrame, sub: pd.DataFrame, 
                    counties_gdf, zone: Optional[pd.DataFrame] = None) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Build lookup tables mapping buses to counties and geographic information.
    
    Parameters:
    -----------
    bus : pd.DataFrame
        Bus data with electrical network information
    bus2sub : pd.DataFrame  
        Bus-to-substation mapping table
    sub : pd.DataFrame
        Substation data with lat/lon coordinates and capacity info
    counties_gdf : gpd.GeoDataFrame
        County boundary polygons
    zone : pd.DataFrame, optional
        Zone definitions for additional geographic mapping
        
    Returns:
    --------
    bus_to_fips : pd.Series
        Mapping from bus_id to county FIPS codes
    bus_local : pd.DataFrame
        Enhanced bus data with geographic information
    """
    # infer key columns
    subcol = next((c for c in ("sub_id", "sub", "subid") if c in bus2sub.columns), None)
    if subcol is None:
        raise KeyError("bus2sub must contain 'sub_id' (or 'sub'/'subid').")

    buscol = next((c for c in ("bus_id", "bus", "bus_idx") if c in bus2sub.columns), None)
    if buscol is None:
        bus2sub_local = bus2sub.copy()
        bus2sub_local["bus"] = bus2sub_local.index
        buscol = "bus"
    else:
        bus2sub_local = bus2sub

    # Create bus to substation mapping
    bus_sub_mapping = bus2sub_local[[buscol, subcol]].rename(columns={buscol: "bus_id", subcol: "sub_id"})
    
    # Check for buses connected to multiple substations (for informational purposes)
    multi_sub_buses = bus_sub_mapping.groupby('bus_id').size()
    multi_sub_count = (multi_sub_buses > 1).sum()
    
    if multi_sub_count > 0:
        print(f"[build_bus_lookup] Found {multi_sub_count} buses connected to multiple substations.")
        print(f"[build_bus_lookup] Using first substation for each bus (deterministic selection).")
        # Keep first substation for each bus
        bus_map = bus_sub_mapping.drop_duplicates(subset='bus_id', keep='first')
    else:
        print(f"[build_bus_lookup] No multi-substation buses found in dataset.")
        # Direct mapping since no multi-substation cases exist
        bus_map = bus_sub_mapping

    # sub lat/lon -> counties
    if gpd is None:
        raise RuntimeError("geopandas required for point-in-polygon county join.")
    if not {"lon", "lat"}.issubset(sub.columns):
        raise KeyError("sub must contain 'lon' and 'lat' columns.")
    sub_gdf = gpd.GeoDataFrame(sub.copy(),
                               geometry=gpd.points_from_xy(sub["lon"], sub["lat"], crs="EPSG:4326"))
    # align CRS
    if counties_gdf.crs is None:
        counties_gdf = counties_gdf.set_crs("EPSG:4269")
    sub_gdf = gpd.sjoin(sub_gdf.to_crs(counties_gdf.crs),
                        counties_gdf[["GEOID", "STATEFP", "NAME", "geometry"]],
                        how="left", predicate="within")

    subid = next((c for c in ("sub_id", "sub", "subid") if c in sub_gdf.columns), None)
    if subid is None:
        sub_gdf = sub_gdf.reset_index().rename(columns={"index": "sub_id"})
        subid = "sub_id"

    sub_to_fips = sub_gdf.set_index(subid)["GEOID"].astype("string")
    sub_to_statefp = sub_gdf.set_index(subid)["STATEFP"].astype("string")
    sub_to_cname = sub_gdf.set_index(subid)["NAME"].astype("string")

    # enriched bus table: bus.csv already has bus_id, so use it directly
    bus_local = bus.copy()
    
    # ensure bus_id is the primary key column name
    if "bus_id" not in bus_local.columns:
        # fallback: create from index or rename from 'bus'
        if "bus" in bus_local.columns:
            bus_local.rename(columns={"bus": "bus_id"}, inplace=True)
        else:
            bus_local = bus_local.reset_index().rename(columns={"index": "bus_id"})

    # merge on bus_id, using suffixes to handle any remaining duplicates
    bus_local = bus_local.merge(bus_map, on="bus_id", how="left", suffixes=("", "_from_bus2sub"))
    
    # clean up any suffixed duplicates
    for col in list(bus_local.columns):
        if col.endswith("_from_bus2sub"):
            base_col = col.replace("_from_bus2sub", "")
            if base_col in bus_local.columns:
                # keep the non-suffixed version, drop the suffixed one
                bus_local.drop(columns=[col], inplace=True)

    # ensure uniqueness of column labels after merge
    if bus_local.columns.duplicated().any():
        dup_names = bus_local.columns[bus_local.columns.duplicated()].tolist()
        print(f"[build_bus_lookup] Dropping duplicate columns after merge: {dup_names}")
        bus_local = bus_local.loc[:, ~bus_local.columns.duplicated()]

    # map county/state attributes from sub-level lookups
    bus_local["county_fips"] = bus_local["sub_id"].map(sub_to_fips)
    bus_local["county_name"] = bus_local["sub_id"].map(sub_to_cname)
    bus_local["state_fips"] = bus_local["sub_id"].map(sub_to_statefp)

    # try to surface zone if present on sub/bus/zone table
    if "zone_id" in sub.columns:
        bus_local["zone_id"] = bus_local["sub_id"].map(sub.set_index("sub_id")["zone_id"])
    elif "zone" in sub.columns:
        bus_local["zone_id"] = bus_local["sub_id"].map(sub.set_index("sub_id")["zone"])
    elif "zone_id" in bus_local.columns:
        pass
    else:
        bus_local["zone_id"] = np.nan

    # add zone names if zone table is available
    if zone is not None and "zone_name" in zone.columns:
        zone_id_col = next((c for c in ("zone_id", "zone") if c in zone.columns), None)
        if zone_id_col:
            zone_lookup = zone.set_index(zone_id_col)["zone_name"]
            bus_local["zone_name"] = bus_local["zone_id"].map(zone_lookup)
        else:
            bus_local["zone_name"] = np.nan
    else:
        bus_local["zone_name"] = np.nan

    # add interconnect names if zone table is available
    if zone is not None and "interconnect" in zone.columns:
        zone_id_col = next((c for c in ("zone_id", "zone") if c in zone.columns), None)
        if zone_id_col:
            interconnect_lookup = zone.set_index(zone_id_col)["interconnect"]
            bus_local["interconnect"] = bus_local["zone_id"].map(interconnect_lookup)
        else:
            bus_local["interconnect"] = np.nan
    else:
        bus_local["interconnect"] = np.nan

        # Drop alias columns that duplicate bus_id values to avoid duplicate label after merge
        if "bus_id" in bus_local.columns:
            for alias in ("bus", "bus_idx"):
                if alias in bus_local.columns:
                    try:
                        if bus_local[alias].astype(str).equals(bus_local["bus_id"].astype(str)):
                            bus_local.drop(columns=[alias], inplace=True)
                    except Exception:
                        # If comparison fails, still drop to prevent merge label collision
                        bus_local.drop(columns=[alias], inplace=True)
    # bus_to_fips series used by other aggregation routines
    bus_to_fips = bus_local.set_index("bus_id")["county_fips"].astype("string")
    return bus_to_fips, bus_local


def aggregate_ac(branch: pd.DataFrame,
                 bus_local: pd.DataFrame,
                 rate_pref="a",
                 pf_mode="none",
                 exclude_transformers=True,
                 keep_intracounty=False) -> pd.DataFrame:
    br = branch.copy()

    # in-service
    for stcol in ("br_status", "status"):
        if stcol in br.columns:
            br = br[br[stcol] == 1].copy()
            break

    # drop transformers via tap/ratio if present
    if exclude_transformers and "ratio" in br.columns:
        br = br[(br["ratio"].isna()) | (br["ratio"] == 0)].copy()

    need = []
    # Check for from/to bus columns with flexible naming
    fbus_col = next((c for c in ("fbus", "from_bus_id", "from_bus") if c in br.columns), None)
    if fbus_col is None:
        need.append("fbus/from_bus_id")
    else:
        br["fbus"] = br[fbus_col]
    
    tbus_col = next((c for c in ("tbus", "to_bus_id", "to_bus") if c in br.columns), None)
    if tbus_col is None:
        need.append("tbus/to_bus_id")
    else:
        br["tbus"] = br[tbus_col]
    
    if "x" not in br.columns:
        need.append("x")
    
    if need:
        raise KeyError(f"branch missing required columns: {need}")

    # attach endpoint metadata
    bmeta = bus_local[["bus_id", "county_fips", "county_name", "state_fips", "zone_id", "zone_name", "interconnect"]].rename(
        columns={"county_fips": "fips", "county_name": "cname", "state_fips": "sfp", "zone_id": "zid", "zone_name": "zname", "interconnect": "interconn"}
    )
    br = br.merge(bmeta.rename(columns={"bus_id": "fbus", "fips": "fips_o", "cname": "cname_o", "sfp": "sfp_o", "zid": "zone_o", "zname": "zname_o", "interconn": "interconn_o"}),
                  on="fbus", how="left")
    br = br.merge(bmeta.rename(columns={"bus_id": "tbus", "fips": "fips_d", "cname": "cname_d", "sfp": "sfp_d", "zid": "zone_d", "zname": "zname_d", "interconn": "interconn_d"}),
                  on="tbus", how="left")
    br = br.dropna(subset=["fips_o", "fips_d"]).copy()
    if not keep_intracounty:
        br = br[br["fips_o"] != br["fips_d"]].copy()

    # normalize rate columns & pick rating
    for col in ("ratea", "rateb", "ratec"):
        if col not in br.columns:
            up = col.upper()
            br[col] = br[up] if up in br.columns else np.nan
    br["rate_mva"] = br.apply(lambda r: pick_rating(r, rate_pref), axis=1)

    # convert to MW (conventions)
    if pf_mode.startswith("const:"):
        try:
            pf = float(pf_mode.split(":", 1)[1])
        except Exception:
            pf = 1.0
        br["cap_mw"] = br["rate_mva"] * pf
        br["pf_used"] = pf
    elif pf_mode == "bykv":
        kv_map = None
        for c in ("base_kv", "basekv", "kv"):
            if c in bus_local.columns:
                kv_map = bus_local.set_index("bus_id")[c]
                break
        if kv_map is not None:
            kv_f = br["fbus"].map(kv_map)
            kv_t = br["tbus"].map(kv_map)
            kv_min = kv_f.combine(kv_t, np.nanmin)
            pf_vals = kv_min.apply(mk_pf_from_kv)
            br["cap_mw"] = br["rate_mva"] * pf_vals
            br["pf_used"] = pf_vals
            br["kv_min"] = kv_min
        else:
            br["cap_mw"] = br["rate_mva"]
            br["pf_used"] = 1.0
    else:
        # DC transport convention: treat MVA limit as active power limit
        br["cap_mw"] = br["rate_mva"]
        br["pf_used"] = 1.0

    # susceptance for DC reduction
    br["B"] = np.where(br["x"] != 0, 1.0 / br["x"], np.nan)

    # unordered county pairs
    pairs = unordered_pair(br, "fips_o", "fips_d")
    br = pd.concat([br, pairs], axis=1)

    # aggregate
    def mode_nonnull(s: pd.Series):
        s = s.dropna()
        return s.mode().iloc[0] if not s.empty else np.nan

    agg = br.groupby(["fips_lo", "fips_hi"], dropna=False).agg(
        Tx_Capacity_MW=("cap_mw", "sum"),
        n_circuits=("cap_mw", "size"),
        sum_rate_mva=("rate_mva", "sum"),
        sum_B_pu=("B", "sum"),
        pf_used_med=("pf_used", "median"),
        kv_min_med=("kv_min", "median") if "kv_min" in br.columns else ("cap_mw", "size"),
        From_County=("cname_o", mode_nonnull),
        To_County=("cname_d", mode_nonnull),
        From_statefp=("sfp_o", mode_nonnull),
        To_statefp=("sfp_d", mode_nonnull),
        From_zone=("zone_o", mode_nonnull),
        To_zone=("zone_d", mode_nonnull),
        From_zone_name=("zname_o", mode_nonnull),
        To_zone_name=("zname_d", mode_nonnull),
        From_interconnect=("interconn_o", mode_nonnull),
        To_interconnect=("interconn_d", mode_nonnull),
    ).reset_index()

    agg["x_eq_pu"] = 1.0 / agg["sum_B_pu"]
    agg["edge_type"] = "AC"

    # rename endpoints & add state abbrev
    agg = agg.rename(columns={"fips_lo": "From_fips", "fips_hi": "To_fips"})
    agg["From_state"] = agg["From_statefp"].astype("string").apply(state_abbrev_from_fips)
    agg["To_state"] = agg["To_statefp"].astype("string").apply(state_abbrev_from_fips)

    # final column order
    first = ["From_fips", "To_fips", "From_County", "To_County", "Tx_Capacity_MW"]
    extras = ["n_circuits", "sum_rate_mva", "sum_B_pu", "x_eq_pu", "pf_used_med", "kv_min_med",
              "edge_type", "From_state", "From_zone", "From_zone_name", "From_interconnect", "To_state", "To_zone", "To_zone_name", "To_interconnect"]
    keep = [c for c in first + extras if c in agg.columns]
    return agg[keep].copy()


def aggregate_hvdc(dcline: Optional[pd.DataFrame],
                   bus_local: pd.DataFrame,
                   keep_intracounty=False) -> Optional[pd.DataFrame]:
    if dcline is None:
        return None

    dc = dcline.copy()
    # normalize expected columns with flexible naming
    f_bus_col = next((c for c in ("f_bus", "from_bus_id", "from_bus") if c in dc.columns), None)
    if f_bus_col and f_bus_col != "f_bus":
        dc["f_bus"] = dc[f_bus_col]
    
    t_bus_col = next((c for c in ("t_bus", "to_bus_id", "to_bus") if c in dc.columns), None)
    if t_bus_col and t_bus_col != "t_bus":
        dc["t_bus"] = dc[t_bus_col]
    
    pmax_col = next((c for c in ("pmax", "Pmax", "PMAX", "p_max") if c in dc.columns), None)
    if pmax_col and pmax_col != "pmax":
        dc["pmax"] = dc[pmax_col]
    if not {"f_bus", "t_bus", "pmax"}.issubset(dc.columns):
        return None

    # filter for in-service lines
    if "status" in dc.columns:
        dc = dc[dc["status"] == 1].copy()
    
    if len(dc) == 0:
        return None

    bmeta = bus_local[["bus_id", "county_fips", "county_name", "state_fips", "zone_id", "zone_name", "interconnect"]].rename(
        columns={"county_fips": "fips", "county_name": "cname", "state_fips": "sfp", "zone_id": "zid", "zone_name": "zname", "interconnect": "interconn"}
    )
    dc = dc.merge(bmeta.rename(columns={"bus_id": "f_bus", "fips": "fips_o", "cname": "cname_o", "sfp": "sfp_o", "zid": "zone_o", "zname": "zname_o", "interconn": "interconn_o"}),
                  on="f_bus", how="left")
    dc = dc.merge(bmeta.rename(columns={"bus_id": "t_bus", "fips": "fips_d", "cname": "cname_d", "sfp": "sfp_d", "zid": "zone_d", "zname": "zname_d", "interconn": "interconn_d"}),
                  on="t_bus", how="left")

    dc = dc.dropna(subset=["fips_o", "fips_d"]).copy()
    if not keep_intracounty:
        dc = dc[dc["fips_o"] != dc["fips_d"]].copy()

    pairs = unordered_pair(dc, "fips_o", "fips_d")
    dc = pd.concat([dc, pairs], axis=1)

    def mode_nonnull(s: pd.Series):
        s = s.dropna()
        return s.mode().iloc[0] if not s.empty else np.nan

    agg = dc.groupby(["fips_lo", "fips_hi"]).agg(
        Tx_Capacity_MW=("pmax", "sum"),
        n_links=("pmax", "size"),
        From_County=("cname_o", mode_nonnull),
        To_County=("cname_d", mode_nonnull),
        From_statefp=("sfp_o", mode_nonnull),
        To_statefp=("sfp_d", mode_nonnull),
        From_zone=("zone_o", mode_nonnull),
        To_zone=("zone_d", mode_nonnull),
        From_zone_name=("zname_o", mode_nonnull),
        To_zone_name=("zname_d", mode_nonnull),
        From_interconnect=("interconn_o", mode_nonnull),
        To_interconnect=("interconn_d", mode_nonnull),
    ).reset_index()

    agg["edge_type"] = "HVDC"
    agg = agg.rename(columns={"fips_lo": "From_fips", "fips_hi": "To_fips"})
    agg["From_state"] = agg["From_statefp"].astype("string").apply(state_abbrev_from_fips)
    agg["To_state"] = agg["To_statefp"].astype("string").apply(state_abbrev_from_fips)

    first = ["From_fips", "To_fips", "From_County", "To_County", "Tx_Capacity_MW"]
    extras = ["n_links", "edge_type", "From_state", "From_zone", "From_zone_name", "From_interconnect", "To_state", "To_zone", "To_zone_name", "To_interconnect"]
    keep = [c for c in first + extras if c in agg.columns]
    return agg[keep].copy()


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="Aggregate inter-county transmission capacity (MW).")
    ap.add_argument("--grid-dir", required=True, help="Path to the base_grid directory")
    ap.add_argument("--output", default="county_edges_tx.csv", help="Output CSV")
    ap.add_argument("--counties-file", default=None, help="Optional local counties file (GeoJSON/Shapefile/GPKG). Must have GEOID.")
    ap.add_argument("--counties-year", type=int, default=2023, help="If not using --counties-file, fetch this Census year (cartographic boundary).")
    ap.add_argument("--rate", default="A", choices=list("ABCabc"), help="Pick rating priority (A/B/C). Default A.")
    ap.add_argument("--pf", default="none",
                    help="MVA→MW rule: 'none' (treat as MW), 'const:0.97', or 'bykv' (<230:0.95, 230–345:0.97, ≥500:0.99).")
    ap.add_argument("--include-transformers", action="store_true", help="Include transformers (tap/ratio != 0). Off by default.")
    ap.add_argument("--keep-intra", action="store_true", help="Keep intra-county (self-loop) lines.")
    ap.add_argument("--no-hvdc", action="store_true", help="Skip HVDC aggregation.")
    args = ap.parse_args()

    bus, branch, sub, bus2sub, zone, dcline = load_grid_tables(args.grid_dir)
    counties = load_counties(args.counties_file, args.counties_year)

    # Build bus→county mapping and enriched bus table
    bus_to_fips, bus_local = build_bus_lookup(bus, bus2sub, sub, counties)

    # AC aggregation
    ac = aggregate_ac(
        branch=branch,
        bus_local=bus_local,
        rate_pref=args.rate,
        pf_mode=args.pf,
        exclude_transformers=(not args.include_transformers),
        keep_intracounty=args.keep_intra
    )

    # HVDC aggregation
    if not args.no_hvdc and dcline is not None:
        dc = aggregate_hvdc(dcline, bus_local, keep_intracounty=args.keep_intra)
        edges = pd.concat([ac, dc], ignore_index=True, sort=False) if dc is not None and len(dc) else ac
    else:
        edges = ac

    # Nice ordering
    order = ["edge_type", "From_state", "From_fips", "From_County", "From_zone", "From_zone_name", "From_interconnect",
             "To_state", "To_fips", "To_County", "To_zone", "To_zone_name", "To_interconnect",
             "Tx_Capacity_MW", "n_circuits", "n_links", "sum_rate_mva", "sum_B_pu", "x_eq_pu",
             "pf_used_med", "kv_min_med"]
    cols = [c for c in order if c in edges.columns] + [c for c in edges.columns if c not in order]
    edges = edges[cols]

    edges.to_csv(args.output, index=False)
    print(f"Wrote {len(edges):,} edges to {args.output}")


if __name__ == "__main__":
    main()
