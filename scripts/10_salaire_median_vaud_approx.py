"""Approximate Vaud median salary, 1981-2025, filling the gaps in the
real (but sparse, biennial, 2012-2024) Vaud data with the shape of the
Swiss national nominal wage index.

`salaire_median_vaud_chf` (from script 09) only has 7 real data points,
every 2 years. This script builds a continuous companion series,
`salaire_median_vaud_approx_chf`, using three techniques depending on
what's available for a given year:

1. Real anchor years (2012, 2014, ..., 2024): the actual value is kept
   as-is.
2. Between two anchors where the CH wage index (script 07) is also
   available for the whole gap (i.e. up to 2020): geometric
   interpolation shaped by the index's year-to-year growth, but
   calibrated to land exactly on both real endpoints. Concretely, for
   a year t between anchors at ya/yb with values Va/Vb:
     fraction = ln(idx(t)/idx(ya)) / ln(idx(yb)/idx(ya))
     value(t) = Va * (Vb/Va) ** fraction
   which reduces to plain geometric (log-linear) interpolation when the
   index isn't available for the gap (2021, 2023 -- the index stops in
   2020), using the time fraction instead of the index-implied one.
3. Before the first anchor (1981-2011) and after the last one (2025),
   there's only one real endpoint to work from:
   - backward: value(t) = V_2012 * idx(t) / idx(2012), using the CH
     index's actual level in year t (available back to 1942).
   - forward (2025 only, past the index's 2020 end): value(t) =
     V_2024 * cagr, where cagr is the compound annual growth rate
     implied by the last two real anchors (2022, 2024).

This is an approximation, not a measurement -- it assumes Vaud salaries
move in step with the Swiss-wide nominal wage index. The `_method`
column records how each value was produced so it's easy to filter down
to real data only.

Output: clean/salaire_median_vaud_approx.csv
        (year, salaire_median_vaud_approx_chf, salaire_median_vaud_approx_method)
"""
import math
import pandas as pd
from _lib import CLEAN

YEAR_MIN, YEAR_MAX = 1981, 2025

anchors_df = pd.read_csv(f"{CLEAN}/salaire_median_vaud.csv")
anchors = dict(zip(anchors_df.year, anchors_df.salaire_median_vaud_chf))
anchor_years = sorted(anchors)

idx_df = pd.read_csv(f"{CLEAN}/wage_index_ch.csv")
idx = dict(zip(idx_df.year, idx_df.wage_index_ch_nominal))


def geometric_interp(year, ya, yb, fraction):
    va, vb = anchors[ya], anchors[yb]
    return va * (vb / va) ** fraction


records = []
for year in range(YEAR_MIN, YEAR_MAX + 1):
    if year in anchors:
        records.append((year, anchors[year], "actual"))
        continue

    prev_anchors = [y for y in anchor_years if y < year]
    next_anchors = [y for y in anchor_years if y > year]

    if prev_anchors and next_anchors:
        ya, yb = prev_anchors[-1], next_anchors[0]
        if year in idx and ya in idx and yb in idx:
            fraction = math.log(idx[year] / idx[ya]) / math.log(idx[yb] / idx[ya])
            method = "interpolated_ch_index"
        else:
            fraction = (year - ya) / (yb - ya)
            method = "interpolated_linear"
        value = geometric_interp(year, ya, yb, fraction)
    elif not prev_anchors:
        # before the first anchor: chain backward off the CH index level
        ya = anchor_years[0]
        value = anchors[ya] * idx[year] / idx[ya]
        method = "extrapolated_ch_index_backward"
    else:
        # after the last anchor, past the CH index's 2020 end: use the
        # most recent observed CAGR between the last two real anchors
        yb = anchor_years[-1]
        ya = anchor_years[-2]
        cagr = (anchors[yb] / anchors[ya]) ** (1 / (yb - ya))
        value = anchors[yb] * cagr ** (year - yb)
        method = "extrapolated_recent_trend"

    records.append((year, value, method))

out = pd.DataFrame(
    records,
    columns=[
        "year",
        "salaire_median_vaud_approx_chf",
        "salaire_median_vaud_approx_method",
    ],
)
out["salaire_median_vaud_approx_chf"] = out["salaire_median_vaud_approx_chf"].round().astype(int)
out.to_csv(f"{CLEAN}/salaire_median_vaud_approx.csv", index=False)
print(f"wrote {len(out)} rows -> clean/salaire_median_vaud_approx.csv "
      f"({out.year.min()}-{out.year.max()})")
print(out["salaire_median_vaud_approx_method"].value_counts())
