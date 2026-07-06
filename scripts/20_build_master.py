"""Merge every clean/*.csv (each keyed by "year") into one master table.

This script is deliberately dumb: it doesn't know what the individual
sources are, it just outer-joins every clean/*.csv on "year". That
means adding a new source later (e.g. Vevey population, or a better
Vaud salary series) only requires dropping a new 0N_*.py script that
writes clean/<name>.csv with a "year" column, then re-running this
script -- no edit needed here.

YEAR_MIN/YEAR_MAX below reflect the explicit choice to keep the full
union of available years (1981-2025) rather than only the intersection
where every column has data; years outside that band (e.g. 2026-2027
GDP forecasts) are dropped so the table doesn't trail off into columns
that are almost entirely empty.

Output: output/vaud_taxes_master.csv
"""
import glob
import pandas as pd
from _lib import CLEAN

YEAR_MIN, YEAR_MAX = 1981, 2025

master = None
for path in sorted(glob.glob(f"{CLEAN}/*.csv")):
    df = pd.read_csv(path)
    assert "year" in df.columns, f"{path} has no 'year' column"
    master = df if master is None else master.merge(df, on="year", how="outer")

master = master[(master.year >= YEAR_MIN) & (master.year <= YEAR_MAX)]
master = master.sort_values("year").reset_index(drop=True)

master.to_csv("output/vaud_taxes_master.csv", index=False)
print(f"wrote {len(master)} rows, {len(master.columns)} columns "
      f"-> output/vaud_taxes_master.csv")
print(master.columns.tolist())
