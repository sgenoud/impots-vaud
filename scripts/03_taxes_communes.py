"""Total raw communal tax revenue across ALL Vaud communes, 1990-2024.

Source: fichiers/a) Ensemble des communes.xlsx
Header (years) is row 2, "Total des impots" row is row 3. Values are
already in raw CHF (not millions).

Output: clean/taxes_communes.csv (year, taxes_communes_chf)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label, row_by_label

SRC = f"{FICHIERS}/a) Ensemble des communes.xlsx"

df = pd.read_excel(SRC, sheet_name=0, header=None)

header_row = 2
total_row = row_by_label(df, "Total des impôts")

records = []
for year_label, value in zip(df.iloc[header_row, 2:], df.iloc[total_row, 2:]):
    year = year_from_label(year_label)
    if year is None or pd.isna(value):
        continue
    records.append({"year": year, "taxes_communes_chf": float(value)})

out = pd.DataFrame(records).sort_values("year")
out.to_csv(f"{CLEAN}/taxes_communes.csv", index=False)
print(f"wrote {len(out)} rows -> clean/taxes_communes.csv "
      f"({out.year.min()}-{out.year.max()})")
