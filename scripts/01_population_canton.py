"""Canton de Vaud population, 1981-2025.

Source: fichiers/Chiffres-cles_Population_depuis-1981.xls (sheet Feuil1)
Row 5 holds the year headers, and the "Total" row right after the
"Population suisse" / "Population étrangère" pair (row 9) holds the
resident population total for each year.

Output: clean/population_canton.csv (year, population_canton)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label, row_by_label

SRC = f"{FICHIERS}/Chiffres-cles_Population_depuis-1981.xls"

df = pd.read_excel(SRC, sheet_name="Feuil1", header=None)

header_row = 5
suisse_row = row_by_label(df, "Population suisse")
total_row = suisse_row + 2
assert df.iloc[total_row, 0] == "Total", (
    f"expected 'Total' two rows below 'Population suisse', got {df.iloc[total_row, 0]!r}"
)

years = df.iloc[header_row, 1:]
values = df.iloc[total_row, 1:]

records = []
for year_label, value in zip(years, values):
    year = year_from_label(year_label)
    if year is None or pd.isna(value):
        continue
    records.append({"year": year, "population_canton": int(value)})

out = pd.DataFrame(records).sort_values("year")
out.to_csv(f"{CLEAN}/population_canton.csv", index=False)
print(f"wrote {len(out)} rows -> clean/population_canton.csv "
      f"({out.year.min()}-{out.year.max()})")
