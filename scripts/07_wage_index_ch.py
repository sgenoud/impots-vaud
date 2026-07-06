"""Swiss (national, NOT Vaud-specific) nominal and real wage index, 1942-2020.

Source: fichiers/ts-x-03.04.03.02.01.csv (OFS "Indice suisse des
salaires nominaux et réels"). This is the only salary-related file
supplied; it is a Switzerland-wide index in points (not a Vaud mean
salary in CHF), and it stops in 2020. It is kept here as a clearly
labeled placeholder/proxy -- swap in real Vaud salary data by writing a
new extraction script and pointing 20_build_master.py at it.

We keep SEX == 'T' (total, both sexes) and pivot WAGE_TYPE N (nominal)
/ R (real) into columns.

Output: clean/wage_index_ch.csv (year, wage_index_ch_nominal, wage_index_ch_real)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN

SRC = f"{FICHIERS}/ts-x-03.04.03.02.01.csv"

df = pd.read_csv(SRC, sep=";", encoding="utf-8-sig")
df.columns = [c.strip('"') for c in df.columns]
df = df[df["SEX"] == "T"]

pivot = df.pivot(index="YEAR", columns="WAGE_TYPE", values="VALUE").reset_index()
pivot = pivot.rename(
    columns={"YEAR": "year", "N": "wage_index_ch_nominal", "R": "wage_index_ch_real"}
)

out = pivot[["year", "wage_index_ch_nominal", "wage_index_ch_real"]].sort_values("year")
out.to_csv(f"{CLEAN}/wage_index_ch.csv", index=False)
print(f"wrote {len(out)} rows -> clean/wage_index_ch.csv "
      f"({out.year.min()}-{out.year.max()})")
