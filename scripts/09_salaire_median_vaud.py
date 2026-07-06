"""Vaud median gross monthly salary (all sectors, all employees), 2012-2024.

Source: fichiers/1_salaire_caracteristique.xlsx, sheet "Tous_secteurs"
("Salaire mensuel brut standardisé selon différentes caractéristiques
des salariés, Vaud, 2012-2024"). This is the Swiss salary structure
survey (RSE/ESS), run every two years, so data points are biennial, not
annual. Note this reports the *median* (not the arithmetic mean) --
that's the standard way this survey is published, since salary
distributions are right-skewed.

Layout: year blocks of 7 columns starting at column 3, each holding
(Total median, Total +/-, Femmes median, Femmes +/-, Hommes median,
Hommes +/-, <blank>); the year label sits on the block's last data
column (row 5). The "Total" row (all positions/education levels
combined) is row 11.

Output: clean/salaire_median_vaud.csv (year, salaire_median_vaud_chf)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label, row_by_label

SRC = f"{FICHIERS}/1_salaire_caracteristique.xlsx"

df = pd.read_excel(SRC, sheet_name="Tous_secteurs", header=None)

YEAR_ROW = 5
total_row = row_by_label(df, "Total")

records = []
for col in df.columns:
    year = year_from_label(df.iloc[YEAR_ROW, col])
    if year is None:
        continue
    median_col = col - 5  # "Total median" column of this year's block
    value = df.iloc[total_row, median_col]
    if pd.isna(value):
        continue
    records.append({"year": year, "salaire_median_vaud_chf": float(value)})

out = pd.DataFrame(records).sort_values("year")
out.to_csv(f"{CLEAN}/salaire_median_vaud.csv", index=False)
print(f"wrote {len(out)} rows -> clean/salaire_median_vaud.csv "
      f"({out.year.min()}-{out.year.max()})")
