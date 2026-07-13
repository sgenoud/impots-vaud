"""Cantonal taxes attributable to natural vs legal persons, per inhabitant,
in units of the estimated annual median Vaud salary, 1990-2024.

The natural-person line combines the income, wealth, and other-natural-person
groups from scripts/02_taxes_canton.py. The legal-person line is the corporate
tax group. Transaction and mobility taxes are intentionally excluded: the
source does not identify their taxpayer, so assigning them to either line
would overstate the comparison.

Output: charts/taxes_canton_personnes_physiques_morales_median_salary.png
        charts/taxes_canton_personnes_physiques_morales_median_salary.csv
"""
import pandas as pd
from _chart_style import RED, new_figure, style_axes, plot_series, add_titles, save

PHYSICAL_DARK = "#1f5fa8"
SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, « Impôts cantonaux selon le type, "
    "Vaud », 1990-2024 ; population : Etat de Vaud / OFS.",
    "Les impôts sur les transactions et sur la mobilité sont exclus : la source "
    "ne permet pas de les attribuer de manière fiable aux personnes physiques "
    "ou morales.",
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS).",
]

PHYSICAL_GROUPS = [
    "taxes_canton_groupe_revenu_personnes_physiques_chf",
    "taxes_canton_groupe_fortune_personnes_physiques_chf",
    "taxes_canton_groupe_autres_personnes_physiques_chf",
]
LEGAL_GROUP = "taxes_canton_groupe_personnes_morales_chf"

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[
    df["population_canton"].notna()
    & df["salaire_median_vaud_approx_chf"].notna()
    & df[LEGAL_GROUP].notna()
].copy()

df["taxes_canton_personnes_physiques_chf"] = df[PHYSICAL_GROUPS].sum(axis=1)
df["taxes_canton_personnes_morales_chf"] = df[LEGAL_GROUP]
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12

for group in ["personnes_physiques", "personnes_morales"]:
    total_column = f"taxes_canton_{group}_chf"
    per_capita_column = f"taxes_canton_{group}_per_capita_chf"
    ratio_column = f"taxes_canton_{group}_median_salary_ratio"
    df[per_capita_column] = df[total_column] / df["population_canton"]
    df[ratio_column] = df[per_capita_column] / df["annual_median_salary_chf"]

csv_columns = [
    "year",
    "taxes_canton_personnes_physiques_chf",
    "taxes_canton_personnes_morales_chf",
    "taxes_canton_personnes_physiques_per_capita_chf",
    "taxes_canton_personnes_morales_per_capita_chf",
    "taxes_canton_personnes_physiques_median_salary_ratio",
    "taxes_canton_personnes_morales_median_salary_ratio",
]
df[csv_columns].to_csv(
    "charts/taxes_canton_personnes_physiques_morales_median_salary.csv", index=False
)

fig, ax = new_figure()
plot_series(ax, df["year"].tolist(), [
    (
        "Personnes physiques",
        PHYSICAL_DARK,
        df["taxes_canton_personnes_physiques_median_salary_ratio"].tolist(),
    ),
    (
        "Personnes morales",
        RED,
        df["taxes_canton_personnes_morales_median_salary_ratio"].tolist(),
    ),
])
style_axes(ax, lambda value, _: f"{value * 100:.1f}%")
ax.set_ylabel("% d'un salaire annuel médian", fontsize=9, color="#898781")
add_titles(
    fig,
    ax,
    "Impôts cantonaux des personnes physiques et morales, en salaires médians",
    "Impôts par habitant, exprimés en part du salaire annuel médian vaudois "
    "(estimé), 1990-2024",
    SOURCE_NOTE,
)
save(fig, "charts/taxes_canton_personnes_physiques_morales_median_salary.png")

print("wrote charts/taxes_canton_personnes_physiques_morales_median_salary.png")
print("wrote charts/taxes_canton_personnes_physiques_morales_median_salary.csv")
