"""Cantonal taxes on natural persons, by category, per inhabitant and in
units of the estimated annual median Vaud salary, 1990-2024.

The source has no annual Vaud mean-salary series; as with the other salary
charts, this uses salaire_median_vaud_approx_chf x 12. The three lines are the
natural-person groupings defined in scripts/02_taxes_canton.py: income,
wealth (including inheritances/donations), and other natural-person taxes.

Output: charts/taxes_canton_personnes_physiques_categories_median_salary.png
        charts/taxes_canton_personnes_physiques_categories_median_salary.csv
"""
import pandas as pd
from _chart_style import new_figure, style_axes, plot_series, add_titles, save

# Related blue shades identify all three series as taxes on natural persons.
PHYSICAL_DARK = "#1f5fa8"
PHYSICAL_MID = "#5b9bd5"
PHYSICAL_LIGHT = "#a7c8e8"

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, « Impôts cantonaux selon le type, "
    "Vaud », 1990-2024 ; population : Etat de Vaud / OFS.",
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS).",
    "Le canton ne publie pas de série annuelle de salaire moyen vaudois ; "
    "l'unité est donc le salaire annuel médian vaudois estimé.",
]

CATEGORIES = [
    (
        "revenu",
        "Impôts sur le revenu",
        PHYSICAL_DARK,
        "taxes_canton_groupe_revenu_personnes_physiques_chf",
    ),
    (
        "fortune",
        "Impôts sur la fortune",
        PHYSICAL_MID,
        "taxes_canton_groupe_fortune_personnes_physiques_chf",
    ),
    (
        "autres",
        "Autres impôts des personnes physiques",
        PHYSICAL_LIGHT,
        "taxes_canton_groupe_autres_personnes_physiques_chf",
    ),
]

df = pd.read_csv("output/vaud_taxes_master.csv")
source_columns = [column for _, _, _, column in CATEGORIES]
df = df[
    df["population_canton"].notna()
    & df["salaire_median_vaud_approx_chf"].notna()
    & df[source_columns].notna().all(axis=1)
].copy()
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12

for key, _, _, source_column in CATEGORIES:
    df[f"taxes_canton_personnes_physiques_{key}_per_capita_chf"] = (
        df[source_column] / df["population_canton"]
    )
    df[f"taxes_canton_personnes_physiques_{key}_median_salary_ratio"] = (
        df[f"taxes_canton_personnes_physiques_{key}_per_capita_chf"]
        / df["annual_median_salary_chf"]
    )

csv_columns = ["year"] + [
    column
    for key, _, _, _ in CATEGORIES
    for column in (
        f"taxes_canton_personnes_physiques_{key}_per_capita_chf",
        f"taxes_canton_personnes_physiques_{key}_median_salary_ratio",
    )
]
df[csv_columns].to_csv(
    "charts/taxes_canton_personnes_physiques_categories_median_salary.csv", index=False
)

fig, ax = new_figure()
plot_series(ax, df["year"].tolist(), [
    (
        label,
        color,
        df[f"taxes_canton_personnes_physiques_{key}_median_salary_ratio"].tolist(),
    )
    for key, label, color, _ in CATEGORIES
])
style_axes(ax, lambda value, _: f"{value * 100:.1f}%")
ax.set_ylabel("% d'un salaire annuel médian", fontsize=9, color="#898781")
add_titles(
    fig,
    ax,
    "Impôts cantonaux des personnes physiques, par catégorie, en salaires médians",
    "Impôts par habitant, exprimés en part du salaire annuel médian vaudois "
    "(estimé), 1990-2024",
    SOURCE_NOTE,
)
save(fig, "charts/taxes_canton_personnes_physiques_categories_median_salary.png")

print("wrote charts/taxes_canton_personnes_physiques_categories_median_salary.png")
print("wrote charts/taxes_canton_personnes_physiques_categories_median_salary.csv")
