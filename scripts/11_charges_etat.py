"""Canton de Vaud total operating expenses ("charges"), 1993-2024.

Two source files cover two different accounting standards, with no
overlapping years:
  - "5.2 Charges de fonctionnement par nature (4p), en francs.xlsx"
    -- old MCH1 standard, 1993-2013
  - "5.2 Charges compte de résultat par nature (4p), en francs.xlsx"
    -- new MCH2 standard, 2014-2024

Both are a nature-code tree (groups 30-39, e.g. "30 personnel", "31
biens et services", ...) with a grand-"Total" row and a "Total" row per
group. The grand total is a clean, continuous series across the
standard switch (CHF 9.27bn in 2013 -> 9.52bn in 2014, a plausible
one-year step), so charges_totales_chf below is safe to read as one
uninterrupted 1993-2024 series.

The by-nature GROUP subtotals are NOT safe to compare across the
switch: MCH2 redefined what the group codes mean (e.g. MCH1's "32
Intérêts passifs" is folded into MCH2's "34 Charges financières", and
MCH1's "34/35/36" transfer/subsidy categories are consolidated into one
MCH2 "36 Charges de transfert"). They're kept as two separate sets of
columns below, suffixed _mch1_chf / _mch2_chf, each populated only for
its own period -- a _mch1 column and a _mch2 column of the same group
number are different definitions, not a continuous series.

Output: clean/charges_etat.csv
  (year, charges_totales_chf, charges_<nature>_mch1_chf..., charges_<nature>_mch2_chf...)
"""
import pandas as pd
from _lib import FICHIERS, CLEAN, year_from_label

MCH1_SRC = f"{FICHIERS}/5.2 Charges de fonctionnement par nature (4p), en francs.xlsx"
MCH2_SRC = f"{FICHIERS}/5.2 Charges compte de résultat par nature (4p), en francs.xlsx"
HEADER_ROW = 3

MCH1_GROUPS = {
    "30": "charges_personnel_mch1_chf",
    "31": "charges_biens_services_mch1_chf",
    "32": "charges_interets_mch1_chf",
    "33": "charges_amortissements_mch1_chf",
    "34": "charges_parts_contributions_mch1_chf",
    "35": "charges_remboursements_collectivites_mch1_chf",
    "36": "charges_aides_subventions_privees_mch1_chf",
    "37": "charges_subventions_redistribuees_mch1_chf",
    "38": "charges_attributions_fonds_mch1_chf",
    "39": "charges_imputations_internes_mch1_chf",
}
MCH2_GROUPS = {
    "30": "charges_personnel_mch2_chf",
    "31": "charges_biens_services_mch2_chf",
    "33": "charges_amortissements_mch2_chf",
    "34": "charges_financieres_mch2_chf",
    "35": "charges_attributions_fonds_mch2_chf",
    "36": "charges_transfert_mch2_chf",
    "37": "charges_subventions_redistribuer_mch2_chf",
    "38": "charges_extraordinaires_mch2_chf",
    "39": "charges_imputations_internes_mch2_chf",
}


def year_columns(df: pd.DataFrame) -> dict[int, int]:
    """Map {year: column index}, reading year labels off HEADER_ROW."""
    cols = {}
    for col in df.columns:
        year = year_from_label(df.iat[HEADER_ROW, col])
        if year is not None:
            cols[year] = col
    return cols


def extract(df, top_mask, groups) -> dict[int, dict[str, float]]:
    cols = year_columns(df)
    total_row = df[top_mask].index[0]
    records: dict[int, dict[str, float]] = {}
    for year, col in cols.items():
        val = df.iat[total_row, col]
        if pd.notna(val):
            records[year] = {"charges_totales_chf": float(val)}

    for code, colname in groups.items():
        rows = df[(df[2].astype(str) == code) & (df[4] == "Total")]
        if rows.empty:
            continue
        row = rows.index[0]
        for year, col in cols.items():
            val = df.iat[row, col]
            if pd.notna(val):
                records.setdefault(year, {})[colname] = float(val)
    return records


df_mch1 = pd.read_excel(MCH1_SRC, sheet_name=0, header=None)
df_mch2 = pd.read_excel(MCH2_SRC, sheet_name=0, header=None)

records = extract(
    df_mch1,
    top_mask=(df_mch1[1] == "CHARGES DE FONCTIONNEMENT") & (df_mch1[2] == "Total"),
    groups=MCH1_GROUPS,
)
mch2_records = extract(
    df_mch2,
    top_mask=(df_mch2[1] == "Charges") & (df_mch2[2] == "Total"),
    groups=MCH2_GROUPS,
)
for year, vals in mch2_records.items():
    records.setdefault(year, {}).update(vals)

out = pd.DataFrame.from_dict(records, orient="index").sort_index()
out.index.name = "year"
out = out.reset_index()
out.to_csv(f"{CLEAN}/charges_etat.csv", index=False)
print(f"wrote {len(out)} rows, {len(out.columns)} columns -> clean/charges_etat.csv "
      f"({out.year.min()}-{out.year.max()})")
