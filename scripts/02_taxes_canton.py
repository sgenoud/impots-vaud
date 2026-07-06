"""Canton de Vaud raw cantonal tax revenue (total), 1990-2024.

Source: fichiers/T18.02.04.xlsx, "Impots cantonaux selon le type, Vaud"
Two sheets cover the period with one year of overlap (2013):
  - "1990-2013": header row 7, "Total" row 26 -> years 1990-2012 kept
  - "2013 et suite": header row 7, "Total" row 23 -> years 2013-2024 kept
    (preferred for 2013 since it's the more recent/refined publication)
Values are originally in millions of CHF; converted to raw CHF here so
all monetary columns in the final table share the same unit.

Output: clean/taxes_canton.csv (year, taxes_canton_chf)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label, row_by_label

SRC = f"{FICHIERS}/T18.02.04.xlsx"
MIO = 1_000_000

records = {}

# --- 1990-2012 from the older sheet ---
df1 = pd.read_excel(SRC, sheet_name="1990-2013", header=None)
total_row1 = row_by_label(df1, "Total")
header_row1 = 7
for year_label, value in zip(df1.iloc[header_row1, 1:], df1.iloc[total_row1, 1:]):
    year = year_from_label(year_label)
    if year is None or year >= 2013 or pd.isna(value):
        continue
    records[year] = float(value) * MIO

# --- 2013-2024 from the newer sheet ---
df2 = pd.read_excel(SRC, sheet_name="2013 et suite", header=None)
total_row2 = row_by_label(df2, "Total")
header_row2 = 7
for year_label, value in zip(df2.iloc[header_row2, 1:], df2.iloc[total_row2, 1:]):
    year = year_from_label(year_label)
    if year is None or pd.isna(value):
        continue
    records[year] = float(value) * MIO

out = pd.DataFrame(
    sorted(records.items()), columns=["year", "taxes_canton_chf"]
)
out.to_csv(f"{CLEAN}/taxes_canton.csv", index=False)
print(f"wrote {len(out)} rows -> clean/taxes_canton.csv "
      f"({out.year.min()}-{out.year.max()})")
