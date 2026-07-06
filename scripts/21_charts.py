"""Build the tax-per-inhabitant charts from output/vaud_taxes_master.csv.

Three charts, same three series (cantonal tax, communal tax, and the two
combined), restricted to the years where both tax series exist
(1990-2024) and, for chart 3, where GDP is also available (1997-2024):

1. taxes_per_capita_chf.png -- CHF per inhabitant (population_canton),
   raw francs.
2. taxes_per_capita_pct_median_salary.png -- the same three series
   expressed as a percentage of one median annual Vaud salary
   (salaire_median_vaud_approx_chf x 12), i.e. "how many median annual
   salaries would it take to cover the per-inhabitant tax bill". This
   uses the *approximated* continuous salary series (script 10), so
   only years 2012/14/16/18/20/22/24 rest on real salary data -- the
   rest follows the Swiss wage index's shape. See README.
3. taxes_per_capita_pct_pib.png -- the same three series expressed as a
   percentage of real GDP (pib_reel_chf, chained to prior-year prices,
   ref. year 2025), i.e. tax revenue as a share of economic output.
   Computed directly as taxes_chf / pib_reel_chf -- population cancels
   out of (taxes/pop) / (pib/pop), so this is the same ratio as
   "per capita tax over per capita GDP" without going through
   population at all. Only 1997-2024, since GDP starts in 1997.

The derived per-capita figures are also written out as
charts/taxes_per_capita.csv so the numbers behind the charts are as
inspectable as everything else in this pipeline.
"""
import pandas as pd
from _chart_style import BLUE, AQUA, YELLOW, new_figure, style_axes, plot_series, add_titles, save

SOURCE_NOTE = (
    "Source : Etat de Vaud, Compte d'Etat (impôt cantonal) ; DGAIC-StatVD, "
    "formulaire des rendements des impôts et taxes communaux (impôts communaux, "
    "ensemble des communes) ; population : Etat de Vaud / OFS."
)

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[df["taxes_canton_chf"].notna() & df["taxes_communes_chf"].notna()].copy()

df["taxes_total_chf"] = df["taxes_canton_chf"] + df["taxes_communes_chf"]
for col in ["taxes_canton_chf", "taxes_communes_chf", "taxes_total_chf"]:
    df[col.replace("_chf", "_per_capita_chf")] = df[col] / df["population_canton"]

df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12
for col in ["taxes_canton_per_capita_chf", "taxes_communes_per_capita_chf", "taxes_total_per_capita_chf"]:
    pct_col = col.replace("_per_capita_chf", "_per_capita_pct_median_salary")
    df[pct_col] = df[col] / df["annual_median_salary_chf"] * 100

for col in ["taxes_canton_chf", "taxes_communes_chf", "taxes_total_chf"]:
    pct_col = col.replace("_chf", "_pct_pib_reel")
    df[pct_col] = df[col] / df["pib_reel_chf"] * 100

derived_cols = [
    "year",
    "taxes_canton_per_capita_chf",
    "taxes_communes_per_capita_chf",
    "taxes_total_per_capita_chf",
    "taxes_canton_per_capita_pct_median_salary",
    "taxes_communes_per_capita_pct_median_salary",
    "taxes_total_per_capita_pct_median_salary",
    "taxes_canton_pct_pib_reel",
    "taxes_communes_pct_pib_reel",
    "taxes_total_pct_pib_reel",
]
df[derived_cols].to_csv("charts/taxes_per_capita.csv", index=False)

x = df["year"].tolist()

# --- Chart 1: CHF per inhabitant ---
fig, ax = new_figure()
plot_series(ax, x, [
    ("Canton", BLUE, df["taxes_canton_per_capita_chf"].tolist()),
    ("Communes (ensemble)", AQUA, df["taxes_communes_per_capita_chf"].tolist()),
    ("Canton + communes", YELLOW, df["taxes_total_per_capita_chf"].tolist()),
])
style_axes(ax, lambda v, _: f"{v:,.0f}".replace(",", "’"))
add_titles(
    fig, ax,
    "Recettes fiscales vaudoises par habitant, 1990-2024",
    "Impôt cantonal, impôt communal (ensemble des communes) et les deux combinés, en CHF par habitant",
    SOURCE_NOTE,
)
ax.set_ylabel("CHF par habitant", fontsize=9, color="#898781")
save(fig, "charts/taxes_per_capita_chf.png")

# --- Chart 2: as a % of the median annual Vaud salary ---
fig, ax = new_figure()
plot_series(ax, x, [
    ("Canton", BLUE, df["taxes_canton_per_capita_pct_median_salary"].tolist()),
    ("Communes (ensemble)", AQUA, df["taxes_communes_per_capita_pct_median_salary"].tolist()),
    ("Canton + communes", YELLOW, df["taxes_total_per_capita_pct_median_salary"].tolist()),
])
style_axes(ax, lambda v, _: f"{v:.0f}%")
add_titles(
    fig, ax,
    "Recettes fiscales vaudoises par habitant, en part du salaire médian",
    "Impôt par habitant rapporté au salaire annuel médian vaudois (estimé), 1990-2024",
    [
        SOURCE_NOTE,
        "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
        "intercalées à l'aide de l'indice suisse des salaires (OFS).",
    ],
)
ax.set_ylabel("% d'un salaire annuel médian", fontsize=9, color="#898781")
save(fig, "charts/taxes_per_capita_pct_median_salary.png")

# --- Chart 3: as a % of real GDP, 1997-2024 ---
df_pib = df[df["pib_reel_chf"].notna()]
x_pib = df_pib["year"].tolist()

fig, ax = new_figure()
plot_series(ax, x_pib, [
    ("Canton", BLUE, df_pib["taxes_canton_pct_pib_reel"].tolist()),
    ("Communes (ensemble)", AQUA, df_pib["taxes_communes_pct_pib_reel"].tolist()),
    ("Canton + communes", YELLOW, df_pib["taxes_total_pct_pib_reel"].tolist()),
])
style_axes(ax, lambda v, _: f"{v:.0f}%")
add_titles(
    fig, ax,
    "Recettes fiscales vaudoises en part du PIB réel",
    "Impôt cantonal, impôt communal (ensemble des communes) et les deux combinés, en % du PIB réel vaudois, 1997-2024",
    [
        SOURCE_NOTE,
        "PIB : Quantitas/HES-SO sur mandat conjoint de l'Etat de Vaud, de la "
        "CVCI et de la BCV (valeur réelle, aux prix de l'année précédente, "
        "année de référence 2025).",
    ],
)
ax.set_ylabel("% du PIB réel", fontsize=9, color="#898781")
save(fig, "charts/taxes_per_capita_pct_pib.png")

print("wrote charts/taxes_per_capita_chf.png")
print("wrote charts/taxes_per_capita_pct_median_salary.png")
print("wrote charts/taxes_per_capita_pct_pib.png")
print("wrote charts/taxes_per_capita.csv")
