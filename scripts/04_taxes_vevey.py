"""Raw communal tax revenue for Vevey, 1990-2024.

Source: fichiers/b) Par communes.xlsx, pre-filtered to a single commune.
We assert that commune is indeed Vevey (BFS no. 5890) so the script
fails loudly if a differently-filtered file is ever dropped in here.
Header (years) is row 5, "Total des impots" row is row 6. Values are
already in raw CHF (not millions).

Output: clean/taxes_vevey.csv (year, taxes_vevey_chf)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label, row_by_label

SRC = f"{FICHIERS}/b) Par communes.xlsx"

df = pd.read_excel(SRC, sheet_name=0, header=None)

commune_label = str(df.iloc[3, 0])
assert "Vevey" in commune_label, (
    f"expected the source file to be filtered to Vevey, got {commune_label!r}"
)

header_row = 5
total_row = row_by_label(df, "Total des impôts")

records = []
for year_label, value in zip(df.iloc[header_row, 2:], df.iloc[total_row, 2:]):
    year = year_from_label(year_label)
    if year is None or pd.isna(value):
        continue
    records.append({"year": year, "taxes_vevey_chf": float(value)})

out = pd.DataFrame(records).sort_values("year")
out.to_csv(f"{CLEAN}/taxes_vevey.csv", index=False)
print(f"wrote {len(out)} rows -> clean/taxes_vevey.csv "
      f"({out.year.min()}-{out.year.max()})")
