"""Compare nominal and real Vaud GDP per inhabitant with the estimated
annual median Vaud salary, 1997-2025.

Dividing GDP by population puts all three series in annual CHF per person.
They therefore share one y-axis (rather than the misleading dual scale needed
for aggregate GDP versus one person's salary). Real GDP is in the source's
chain-price, 2025-reference basis; nominal GDP and salary are current CHF.

Output: charts/pib_par_habitant_salaire_median.png
        charts/pib_par_habitant_salaire_median.csv
"""
import pandas as pd
from matplotlib.lines import Line2D
from _chart_style import BLUE, GREEN, RED, INK_MUTED, new_figure, style_axes, add_titles, save

SOURCE_NOTE = [
    "PIB : Quantitas/HES-SO, mandat conjoint Etat de Vaud / CVCI / BCV "
    "(valeurs nominale et réelle) ; population : Etat de Vaud / OFS.",
    "Le PIB réel est aux prix de l'année précédente, année de référence 2025. "
    "Les points rouges indiquent les années d'observation effective du salaire "
    "vaudois ; les autres années sont estimées à l'aide de l'indice suisse des "
    "salaires (OFS).",
]

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[
    df["pib_nominal_chf"].notna()
    & df["pib_reel_chf"].notna()
    & df["population_canton"].notna()
    & df["salaire_median_vaud_approx_chf"].notna()
].copy()
df["pib_nominal_par_habitant_chf"] = df["pib_nominal_chf"] / df["population_canton"]
df["pib_reel_par_habitant_chf"] = df["pib_reel_chf"] / df["population_canton"]
df["salaire_median_vaud_annuel_chf"] = df["salaire_median_vaud_approx_chf"] * 12

df[[
    "year", "pib_nominal_par_habitant_chf", "pib_reel_par_habitant_chf",
    "salaire_median_vaud_annuel_chf", "salaire_median_vaud_approx_method",
]].to_csv("charts/pib_par_habitant_salaire_median.csv", index=False)

fig, ax = new_figure()
ax.plot(
    df["year"], df["pib_nominal_par_habitant_chf"], color=BLUE, linewidth=2,
    solid_capstyle="round", zorder=3,
)
ax.plot(
    df["year"], df["pib_reel_par_habitant_chf"], color=GREEN, linewidth=2,
    solid_capstyle="round", zorder=3,
)
ax.plot(
    df["year"], df["salaire_median_vaud_annuel_chf"], color=RED, linewidth=2,
    solid_capstyle="round", zorder=3,
)
actual_salary = df[df["salaire_median_vaud_approx_method"] == "actual"]
ax.scatter(
    actual_salary["year"], actual_salary["salaire_median_vaud_annuel_chf"],
    color=RED, edgecolor="#fcfcfb", linewidth=0.8, s=30, zorder=4,
)
style_axes(ax, lambda value, _: f"{value / 1_000:.0f}k")
ax.set_ylabel("CHF par habitant / an", fontsize=9, color=INK_MUTED)
ax.legend(
    handles=[
        Line2D([0], [0], color=BLUE, linewidth=2, label="PIB nominal par habitant"),
        Line2D([0], [0], color=GREEN, linewidth=2, label="PIB réel par habitant"),
        Line2D([0], [0], color=RED, linewidth=2, marker="o", markersize=5,
               markeredgecolor="#fcfcfb", label="Salaire annuel médian estimé (point = observation)"),
    ],
    loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False,
    fontsize=8, labelcolor=INK_MUTED,
)
add_titles(
    fig,
    ax,
    "PIB vaudois par habitant et salaire médian",
    "PIB nominal, PIB réel et salaire annuel médian estimé, 1997-2025",
    SOURCE_NOTE,
)
save(fig, "charts/pib_par_habitant_salaire_median.png")

print("wrote charts/pib_par_habitant_salaire_median.png")
print("wrote charts/pib_par_habitant_salaire_median.csv")
