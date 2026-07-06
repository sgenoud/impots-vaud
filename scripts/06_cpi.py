"""Swiss consumer price index (IPC), annual average, 1977-2025.

Source: fichiers/T05.01.01.xlsx, sheet "Base Déc_1982" (base December
1982 = 100). This single sheet already spans the full 30-35 year window
we need, so there's no need to chain across the file's other rebased
sheets. Column 0 holds the year, column 13 the annual average
("Moyenne annuelle"); blank rows are spacers in the source and are
skipped.

Output: clean/cpi.csv (year, cpi_dec1982_base100)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label

SRC = f"{FICHIERS}/T05.01.01.xlsx"

df = pd.read_excel(SRC, sheet_name="Base Déc_1982", header=None)

ANNUAL_AVG_COL = 13

records = []
for _, row in df.iterrows():
    year = year_from_label(row[0])
    value = row[ANNUAL_AVG_COL]
    if year is None or pd.isna(value):
        continue
    records.append({"year": year, "cpi_dec1982_base100": float(value)})

out = pd.DataFrame(records).sort_values("year")
out.to_csv(f"{CLEAN}/cpi.csv", index=False)
print(f"wrote {len(out)} rows -> clean/cpi.csv ({out.year.min()}-{out.year.max()})")
