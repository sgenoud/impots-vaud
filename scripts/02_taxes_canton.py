"""Extract the full table of cantonal tax revenue by type, 1990-2024.

Source: fichiers/T18.02.04.xlsx, "Impôts cantonaux selon le type, Vaud".
The source publishes two layouts.  The 1990-2013 sheet supplies 1990-2012;
the newer 2013-et-suite sheet supplies 2013-2024 (including the overlapping
2013 observation).  Every source line is retained in a separate column.  A
blank in a detailed column means that line did not exist in that layout -- it
is not a zero.

The six ``taxes_canton_groupe_*`` columns are documented broad
classifications for the stacked chart. The transaction group is calculated
against the source Total so all six groups reconcile exactly, including the
source's non-additive recovered-tax memo line. Values are converted from
millions to raw CHF.

Output: clean/taxes_canton.csv
"""
import math

import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label, row_by_label

SRC = f"{FICHIERS}/T18.02.04.xlsx"
MIO = 1_000_000

# Stable column name -> exact source label in each of the two layouts.  The
# layouts have genuinely different detail classifications after 2013, so we
# keep both rather than pretending that, for example, old "gains immobiliers"
# and new "gains en capital" are the same source line.
RAW_LINES = {
    "impot_revenu_pp": ("Impôt sur le revenu (1)", "Impôts sur le revenu"),
    "impot_fortune_pp": ("Impôt sur la fortune (1)", "Impôts sur la fortune"),
    "impot_source_pp": ("Impôt à la source (1)", "Impôts à la source"),
    "impot_special_etrangers_pp": ("Impôt spécial des étrangers (1)", None),
    "autres_impots_directs_pp": (None, "Autres impôts directs (pers. physiques)"),
    "impot_benefice_pm": ("Impôt sur le bénéfice net (1)", "Impôts sur les bénéfices"),
    "impot_capital_pm": ("Impôt sur le capital (1)", "Impôts sur le capital"),
    "impot_complementaire_immeubles_pm": ("Impôt complémentaire sur les immeubles", None),
    "autres_impots_directs_pm": (None, "Autres impôts directs (pers. morales)"),
    "impot_gains_immobiliers": ("Impôt sur les gains immobiliers", None),
    "impot_gains_capital": (None, "Impôts sur les gains en capital"),
    "droits_mutation": ("Droits de mutation", None),
    "droits_timbre": ("Droits de timbre", None),
    "droits_mutation_timbre": (None, "Droits de mutation et timbre"),
    "impot_successions_donations": (
        "Impôt sur les successions et donations", "Impôts sur les successions et donations"
    ),
    "impot_chiens": ("Impôt sur les chiens", "Impôt sur les chiens"),
    "impot_tombolas_loteries": ("Impôt sur les tombolas et les loteries", None),
    "impot_appareils_automatiques": ("Impôt sur les appareils automatiques (2)", None),
    "taxes_vehicules_bateaux_cycles": ("Taxes sur les véhic., bateaux et cyclo.", None),
    "taxes_routieres": (None, "Taxes routières"),
    "impot_bateaux": (None, "Impôt sur les bateaux"),
    "impot_recupere_apres_defalcation": ("Impôt récupéré après défalcation", None),
}

# These are deliberately broad taxpayer/type groups. Transactions is
# calculated as a residual below, keeping the stack complete even where the
# source's "impôt récupéré après défalcation" memo line is not additive.
GROUPS = {
    "revenu_personnes_physiques": [
        "impot_revenu_pp", "impot_source_pp", "impot_special_etrangers_pp",
    ],
    "fortune_personnes_physiques": [
        "impot_fortune_pp", "impot_successions_donations",
    ],
    "autres_personnes_physiques": [
        "autres_impots_directs_pp", "impot_gains_immobiliers", "impot_gains_capital",
        "impot_chiens", "impot_tombolas_loteries",
    ],
    "personnes_morales": [
        "impot_benefice_pm", "impot_capital_pm", "impot_complementaire_immeubles_pm",
        "autres_impots_directs_pm", "impot_appareils_automatiques",
    ],
    "mobilite": [
        "taxes_vehicules_bateaux_cycles", "taxes_routieres", "impot_bateaux",
    ],
    "transactions": [
        "droits_mutation", "droits_timbre", "droits_mutation_timbre",
    ],
}


def extract_sheet(sheet_name: str, label_index: int, keep_year) -> dict[int, dict[str, float]]:
    """Read one layout, failing loudly if a declared source row disappears."""
    df = pd.read_excel(SRC, sheet_name=sheet_name, header=None)
    header_row = 7
    years = [year_from_label(value) for value in df.iloc[header_row, 1:]]
    rows = {
        key: row_by_label(df, label)
        for key, labels in RAW_LINES.items()
        if (label := labels[label_index]) is not None
    }
    total_row = row_by_label(df, "Total")

    result = {}
    for column, year in enumerate(years, start=1):
        if year is None or not keep_year(year):
            continue
        record = {}
        for key, row in rows.items():
            value = df.iloc[row, column]
            # The source uses an ellipsis for unavailable early values; retain
            # that as a missing detailed value rather than coercing it to zero.
            try:
                record[f"taxes_canton_{key}_chf"] = float(value) * MIO
            except (TypeError, ValueError):
                record[f"taxes_canton_{key}_chf"] = float("nan")
        record["taxes_canton_chf"] = float(df.iloc[total_row, column]) * MIO
        result[year] = record
    return result


records = {}
records.update(extract_sheet("1990-2013", 0, lambda year: year < 2013))
records.update(extract_sheet("2013 et suite", 1, lambda year: year >= 2013))

raw_columns = [f"taxes_canton_{key}_chf" for key in RAW_LINES]
out = pd.DataFrame.from_dict(records, orient="index").rename_axis("year").reset_index()
out = out.reindex(columns=["year", *raw_columns, "taxes_canton_chf"])

# All groups except Transactions map directly to source lines. Transactions
# is the remaining source Total, so it contains transaction taxes while also
# correctly absorbing the non-additive recovered-tax memo line in the older
# layout.
for group, members in GROUPS.items():
    if group == "transactions":
        continue
    member_columns = [f"taxes_canton_{member}_chf" for member in members]
    out[f"taxes_canton_groupe_{group}_chf"] = out[member_columns].fillna(0).sum(axis=1)

core_group_columns = [
    f"taxes_canton_groupe_{group}_chf"
    for group in GROUPS if group != "transactions"
]
out["taxes_canton_groupe_transactions_chf"] = (
    out["taxes_canton_chf"] - out[core_group_columns].sum(axis=1)
)
group_columns = [f"taxes_canton_groupe_{group}_chf" for group in GROUPS]
reconstructed_total = out[group_columns].sum(axis=1)
for year, expected, actual in zip(out["year"], out["taxes_canton_chf"], reconstructed_total):
    if not math.isclose(expected, actual, rel_tol=0, abs_tol=1):
        raise ValueError(
            f"Detailed lines do not reconcile to Total in {year}: "
            f"{actual:,.2f} CHF vs {expected:,.2f} CHF"
        )

out.to_csv(f"{CLEAN}/taxes_canton.csv", index=False)
print(f"wrote {len(out)} rows and {len(out.columns)} columns -> clean/taxes_canton.csv "
      f"({out.year.min()}-{out.year.max()})")
