"""Subsides cantonaux aux primes d'assurance-maladie (LAMal), par type de
bénéficiaire, 1986-2024.

Source: fichiers/subsides-francs.xlsx, sheet "Serie" -- "Dépenses en
francs pour les subsides aux primes d'assurance-maladie par type de
bénéficiaires, Vaud, 1986-2024" (DGCS / Office vaudois de
l'assurance-maladie). Values are already raw CHF (the filename says
"francs", not "milliers"), so no unit conversion is needed, unlike most
other sources in this pipeline.

4 beneficiary-type columns, which sum exactly to the source's own Total
column every year (checked below) -- no residual needed:
  - Prestations complémentaires à l'AVS et à l'AI
  - RI (revenu d'insertion) et assimilés / cas de rigueur -- doesn't
    exist before 1996 (source uses "–" for those years)
  - Subsidiés partiels
  - Collectif personnes âgées -- discontinued after 1995, when LAMal
    took effect in 1996 (source uses "–" or a blank cell from 1996 on)
These two are complementary in time (one stops the year the other
starts), reflecting the 1996 LAMal reform, not a data gap.

This is a different source than charges_transfert_prevoyance_maladie_accident_chf
(scripts/12_charges_transfert_fonctionnel.py) -- related (both are
health-related transfer spending) but not cross-checked against each
other here, since their scope may well differ (this one is specifically
LAMal premium subsidies; the MCH2 functional line may be broader).

Output: clean/subsides_maladie.csv
  (year, subsides_maladie_pc_avs_ai_chf, subsides_maladie_ri_cas_rigueur_chf,
   subsides_maladie_partiels_chf, subsides_maladie_collectif_agees_chf,
   subsides_maladie_total_chf)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN

SRC = f"{FICHIERS}/subsides-francs.xlsx"

COLUMNS = {
    1: "subsides_maladie_pc_avs_ai_chf",
    2: "subsides_maladie_ri_cas_rigueur_chf",
    3: "subsides_maladie_partiels_chf",
    4: "subsides_maladie_collectif_agees_chf",
    5: "subsides_maladie_total_chf",
}

df = pd.read_excel(SRC, sheet_name="Serie", header=None)


def to_float(v):
    if isinstance(v, str) or pd.isna(v):
        return None
    return float(v)


records = []
for _, row in df.iterrows():
    year = row[0]
    if not isinstance(year, (int, float)) or pd.isna(year):
        continue
    record = {"year": int(year)}
    for col, name in COLUMNS.items():
        record[name] = to_float(row[col])
    records.append(record)

out = pd.DataFrame(records).sort_values("year")

# The 4 beneficiary-type columns should sum almost exactly to the
# source's own Total column every year (off by CHF 1 in 2011/2012 --
# rounding in the source, not an extraction bug).
named_cols = [c for c in COLUMNS.values() if c != "subsides_maladie_total_chf"]
named_sum = out[named_cols].sum(axis=1, min_count=1)
mismatch = (named_sum - out["subsides_maladie_total_chf"]).abs()
assert (mismatch.dropna() < 2).all(), (
    f"beneficiary-type columns don't sum to the source's Total:\n"
    f"{out[mismatch >= 2]}"
)

out.to_csv(f"{CLEAN}/subsides_maladie.csv", index=False)
print(f"wrote {len(out)} rows, {len(out.columns)} columns -> "
      f"clean/subsides_maladie.csv ({out.year.min()}-{out.year.max()})")
