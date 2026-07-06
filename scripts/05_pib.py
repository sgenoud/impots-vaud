"""Vaud GDP (PIB vaudois), nominal and real, 1997 onward.

Source: fichiers/PIB-VD_nominal_depuis_1997.xlsx and
        fichiers/PIB-VD_reel_depuis_1997.xlsx
Each file's first table (absolute values, not growth-rate %) has the
year header on row 7 and the "PIB vaudois" total on row 26 (real GDP is
chained to previous-year prices, reference year 2025). Note the nominal
sheet runs 1997-2025(p) while the real sheet also carries 2026-2027,
marked with '*' as forecasts -- those are kept here and filtered later
by the master build if out of range. Values are originally in millions
of CHF; converted to raw CHF here to match the other monetary columns.

Output: clean/pib.csv (year, pib_nominal_chf, pib_reel_chf)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label, row_by_label

MIO = 1_000_000
HEADER_ROW = 7


def extract(path: str) -> dict[int, float]:
    df = pd.read_excel(path, sheet_name=0, header=None)
    total_row = row_by_label(df, "PIB vaudois")
    out = {}
    for year_label, value in zip(df.iloc[HEADER_ROW, 2:], df.iloc[total_row, 2:]):
        year = year_from_label(year_label)
        if year is None or pd.isna(value) or value == "…":
            continue
        out[year] = float(value) * MIO
    return out


nominal = extract(f"{FICHIERS}/PIB-VD_nominal_depuis_1997.xlsx")
reel = extract(f"{FICHIERS}/PIB-VD_reel_depuis_1997.xlsx")

years = sorted(set(nominal) | set(reel))
out = pd.DataFrame(
    {
        "year": years,
        "pib_nominal_chf": [nominal.get(y) for y in years],
        "pib_reel_chf": [reel.get(y) for y in years],
    }
)
out.to_csv(f"{CLEAN}/pib.csv", index=False)
print(f"wrote {len(out)} rows -> clean/pib.csv ({out.year.min()}-{out.year.max()})")
