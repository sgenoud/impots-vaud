"""Build the Vevey tax-per-inhabitant charts from output/vaud_taxes_master.csv.

Mirrors scripts/21_charts.py but for Vevey alone (a single series, since
there's no canton/communes split at commune level): taxes_vevey_chf per
population_vevey, restricted to 1990-2024 where taxes_vevey_chf exists.

taxes_vevey_per_capita_pct_median_salary.png expresses that series as a
percentage of one median annual Vaud salary
(salaire_median_vaud_approx_chf x 12). Uses the *approximated*
continuous salary series (script 10) -- only 2012/14/16/18/20/22/24
rest on real salary data, the rest follows the Swiss wage index's
shape. See README. Note this compares a commune-level tax figure to
a canton-level salary figure, since no Vevey-specific salary data
exists.

The derived figures (including the plain CHF-per-inhabitant one, which
no longer has its own chart) are still written out as
charts/taxes_vevey_per_capita.csv for inspection.
"""
import pandas as pd
from _chart_style import GREEN, new_figure, style_axes, plot_series, add_titles, save

SOURCE_NOTE = (
    "Source : DGAIC-StatVD, formulaire des rendements des impôts et taxes "
    "communaux (impôt communal de Vevey) ; population : OFS (ESPOP/STATPOP) "
    "et Etat de Vaud (StatVD)."
)

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[df["taxes_vevey_chf"].notna()].copy()

df["taxes_vevey_per_capita_chf"] = df["taxes_vevey_chf"] / df["population_vevey"]
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12
df["taxes_vevey_per_capita_pct_median_salary"] = (
    df["taxes_vevey_per_capita_chf"] / df["annual_median_salary_chf"] * 100
)

derived_cols = [
    "year",
    "taxes_vevey_per_capita_chf",
    "taxes_vevey_per_capita_pct_median_salary",
]
df[derived_cols].to_csv("charts/taxes_vevey_per_capita.csv", index=False)

x = df["year"].tolist()

# --- Chart 1: as a % of the median annual Vaud salary ---
fig, ax = new_figure()
plot_series(ax, x, [
    ("Vevey", GREEN, df["taxes_vevey_per_capita_pct_median_salary"].tolist()),
])
style_axes(ax, lambda v, _: f"{v:.1f}%")
add_titles(
    fig, ax,
    "Recettes fiscales communales de Vevey par habitant, en part du salaire médian",
    "Impôt par habitant de Vevey rapporté au salaire annuel médian vaudois (estimé), 1990-2024",
    [
        SOURCE_NOTE,
        "Salaire : OFS, Enquête suisse sur la structure des salaires (salaire "
        "cantonal, non spécifique à Vevey) ; années intercalées à l'aide de "
        "l'indice suisse des salaires (OFS).",
    ],
)
ax.set_ylabel("% d'un salaire annuel médian", fontsize=9, color="#898781")
save(fig, "charts/taxes_vevey_per_capita_pct_median_salary.png")

print("wrote charts/taxes_vevey_per_capita_pct_median_salary.png")
print("wrote charts/taxes_vevey_per_capita.csv")
