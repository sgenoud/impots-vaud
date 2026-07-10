"""Charges de transfert (MCH2 nature group 36), broken down by functional
classification (what the money is spent ON -- health, education, social
welfare, ... -- rather than what kind of expense it is), 2014-2025.

Source: fichiers/Charges_de_transfert_par_classification_fonctionnelle.xlsx
One row per top-level functional code (single digit, 0-9) plus indented
sub-codes (two digits) and a "TOTAL" row; the 10 top-level rows are kept
here, matching the level of detail scripts/24_charges_main_categories.py
etc. work at, plus the 6 sub-codes under "5 Prévoyance sociale" (51/52/
53/54/55/57 -- 56/58/59 don't exist in this classification), since
that's the biggest function and scripts/28-29 already established it's
the main driver of the charges-de-transfert increase. Unlike the
top-level residual in script 28, no "Autres" bucket is needed for these
6: they sum exactly to charges_transfert_prevoyance_sociale_chf (checked
below), since 51/52/53/54/55/57 is a complete partition of code "5" in
this source. Values are in thousands of CHF in the source; converted to
raw CHF here, same convention as every other monetary column.

The source's TOTAL row is cross-checked against charges_transfert_mch2_chf
(scripts/11_charges_etat.py) for every year both cover (2014-2024) -- they
should match, since this file breaks the exact same MCH2 group down a
different way. This file additionally has 2025, which the general "5.2"
charges report doesn't yet -- kept here since population_canton and
salaire_median_vaud_approx_chf both already reach 2025, so a 2025 row is
still usable for the per-capita / median-salary-ratio charts, even though
charges_totales_chf itself has no 2025 value to compare against.

Output: clean/charges_transfert_fonctionnel.csv
  (year, charges_transfert_<fonction>_chf..., charges_transfert_fonc_total_chf,
   charges_transfert_prevoyance_<sous-fonction>_chf...)
"""
import re
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label

SRC = f"{FICHIERS}/Charges_de_transfert_par_classification_fonctionnelle.xlsx"
HEADER_ROW = 0
MIO = 1_000  # source values are in thousands of CHF

FUNCTIONS = {
    "0": "charges_transfert_administration_generale_chf",
    "1": "charges_transfert_ordre_securite_chf",
    "2": "charges_transfert_formation_chf",
    "3": "charges_transfert_culture_sport_loisirs_eglise_chf",
    "4": "charges_transfert_sante_chf",
    "5": "charges_transfert_prevoyance_sociale_chf",
    "6": "charges_transfert_trafic_telecom_chf",
    "7": "charges_transfert_protection_environnement_chf",
    "8": "charges_transfert_economie_publique_chf",
    "9": "charges_transfert_finances_impots_chf",
}
PREVOYANCE_SUBFUNCTIONS = {
    "51": "charges_transfert_prevoyance_maladie_accident_chf",
    "52": "charges_transfert_prevoyance_invalidite_chf",
    "53": "charges_transfert_prevoyance_vieillesse_survivants_chf",
    "54": "charges_transfert_prevoyance_famille_jeunesse_chf",
    "55": "charges_transfert_prevoyance_chomage_chf",
    "57": "charges_transfert_prevoyance_aide_sociale_asile_chf",
}

df = pd.read_excel(SRC, sheet_name=0, header=None)

year_cols = {}
for col in df.columns:
    year = year_from_label(df.iat[HEADER_ROW, col])
    if year is not None:
        year_cols[year] = col

records: dict[int, dict[str, float]] = {}


def extract_codes(codes: dict[str, str]) -> None:
    for code, colname in codes.items():
        rows = df[df[0].astype(str).str.fullmatch(re.escape(code))]
        assert len(rows) == 1, f"expected exactly one row for code {code!r}, got {len(rows)}"
        row = rows.index[0]
        for year, col in year_cols.items():
            val = df.iat[row, col]
            if pd.notna(val):
                records.setdefault(year, {})[colname] = float(val) * MIO


extract_codes(FUNCTIONS)
extract_codes(PREVOYANCE_SUBFUNCTIONS)

total_row = df[df[0].astype(str) == "TOTAL"].index[0]
for year, col in year_cols.items():
    val = df.iat[total_row, col]
    if pd.notna(val):
        records.setdefault(year, {})["charges_transfert_fonc_total_chf"] = float(val) * MIO

out = pd.DataFrame.from_dict(records, orient="index").sort_index()
out.index.name = "year"
out = out.reset_index()

# Sanity check against scripts/11_charges_etat.py's charges_transfert_mch2_chf
# for the years both sources cover. Tolerance is 2000 CHF, not 0: this
# source rounds to the nearest thousand CHF per functional line before
# summing to TOTAL, so a few hundred CHF of rounding drift versus the
# nature-based total (computed from unrounded francs) is expected.
etat = pd.read_csv(f"{CLEAN}/charges_etat.csv")[["year", "charges_transfert_mch2_chf"]]
check = out.merge(etat, on="year", how="inner")
mismatch = (check["charges_transfert_fonc_total_chf"] - check["charges_transfert_mch2_chf"]).abs()
assert (mismatch < 2000).all(), (
    f"functional-classification TOTAL doesn't match charges_transfert_mch2_chf:\n"
    f"{check[mismatch >= 2000]}"
)

# The 6 Prévoyance sociale sub-functions should sum almost exactly to the
# parent (51/52/53/54/55/57 is a complete partition -- no "Autres"
# needed). Tolerance is 1500 CHF, not 0, for the same source-rounding
# reason as the check above (occasionally off by CHF 1000, i.e. a
# rounding-to-the-nearest-thousand difference on one sub-line).
sub_sum = out[list(PREVOYANCE_SUBFUNCTIONS.values())].sum(axis=1, min_count=1)
sub_mismatch = (sub_sum - out["charges_transfert_prevoyance_sociale_chf"]).abs()
assert (sub_mismatch.dropna() < 1500).all(), (
    f"Prévoyance sociale sub-functions don't sum to the parent:\n"
    f"{out[sub_mismatch >= 1500]}"
)

out.to_csv(f"{CLEAN}/charges_transfert_fonctionnel.csv", index=False)
print(f"wrote {len(out)} rows, {len(out.columns)} columns -> "
      f"clean/charges_transfert_fonctionnel.csv ({out.year.min()}-{out.year.max()})")
