"""100%-stacked cantonal tax revenue by broad taxpayer/type classification.

The detailed source table is extracted by scripts/02_taxes_canton.py.  This
chart deliberately uses six broad groups so the stack remains readable over
35 years while still reconciling to the source Total. Transaction and mobility
taxes are shown explicitly rather than placed in an "Autres" bucket. Each
year's stack is normalised to that year's Total, so it shows composition
rather than the increase in nominal receipts.

Output: charts/taxes_canton_par_type.png
        charts/taxes_canton_par_type.csv
"""
import pandas as pd
from matplotlib.patches import Patch
from _chart_style import (
    YELLOW, VIOLET, RED,
    new_figure, style_axes, add_titles, save,
)

# Three shades of one blue hue make the physical-person taxes read as one
# family. Corporate taxes deliberately use a contrasting red.
PHYSICAL_DARK = "#1f5fa8"
PHYSICAL_MID = "#5b9bd5"
PHYSICAL_LIGHT = "#a7c8e8"

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, « Impôts cantonaux selon le type, "
    "Vaud », 1990-2024. Montants en francs, convertis depuis les millions.",
    "Les groupes sont construits à partir des lignes détaillées ; « Transactions » "
    "est le solde jusqu'à la ligne « Total » de la source.",
    "La publication change de présentation en 2013 ; cette année provient de "
    "la feuille 2013-2024, retenue à la place de la version plus ancienne.",
]

# Bottom-to-top order of the stack. The two non-taxpayer classifications are
# explicit, leaving no generic "Autres" category.
GROUPS = [
    ("mobilite", "Impôts sur la mobilité", YELLOW),
    ("transactions", "Impôts sur les transactions", VIOLET),
    ("personnes_morales", "Impôts des personnes morales", RED),
    ("autres_personnes_physiques", "Autres impôts des personnes physiques", PHYSICAL_LIGHT),
    ("fortune_personnes_physiques", "Impôts sur la fortune des personnes physiques", PHYSICAL_MID),
    ("revenu_personnes_physiques", "Impôts sur le revenu des personnes physiques", PHYSICAL_DARK),
]

chf_columns = [f"taxes_canton_groupe_{key}_chf" for key, _, _ in GROUPS]
df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[df["taxes_canton_chf"].notna()].copy()

if not (df[chf_columns].sum(axis=1).round(2) == df["taxes_canton_chf"].round(2)).all():
    raise ValueError("Tax groups must reconcile to taxes_canton_chf before charting")

pct_columns = []
for key, _, _ in GROUPS:
    pct_column = f"taxes_canton_groupe_{key}_pct_total"
    df[pct_column] = df[f"taxes_canton_groupe_{key}_chf"] / df["taxes_canton_chf"] * 100
    pct_columns.append(pct_column)

# This CSV retains the CHF components and adds the exact chart values.
# clean/taxes_canton.csv keeps every original source line for full inspection.
derived_columns = ["year", *chf_columns, "taxes_canton_chf", *pct_columns]
df[derived_columns].to_csv("charts/taxes_canton_par_type.csv", index=False)

if not (df[pct_columns].sum(axis=1).round(10) == 100).all():
    raise ValueError("Tax group shares must sum to 100% before charting")

fig, ax = new_figure()
years = df["year"].tolist()
ax.stackplot(
    years,
    *[df[column].tolist() for column in pct_columns],
    colors=[color for _, _, color in GROUPS],
    alpha=0.88,
    linewidth=0.5,
    edgecolor="#fcfcfb",
    zorder=2,
)

# The source's layout changes here.  It is marked rather than treating it as
# a missing year or a change in the total series.
ax.axvline(2013, color="#898781", linewidth=1, linestyle=(0, (2, 2)), zorder=4)
ax.annotate("nouvelle classification source", xy=(2013, 0), xytext=(4, 5),
            textcoords="offset points", color="#898781", fontsize=7, rotation=90,
            va="bottom")
ax.set_ylim(0, 100)
style_axes(ax, lambda value, _: f"{value:.0f}%")
ax.set_ylabel("Part du total annuel", fontsize=9, color="#898781")

# A stacked area has no meaningful independent end value for direct labels;
# the legend maps each coloured band to its group instead.
handles = [Patch(facecolor=color, label=label) for _, label, color in reversed(GROUPS)]
ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0),
          frameon=False, fontsize=8, labelcolor="#52514e", handlelength=1.2)

add_titles(
    fig,
    ax,
    "Composition des impôts cantonaux vaudois, par type de contribuable",
    "Part de chaque grande catégorie dans le total annuel des recettes fiscales, 1990-2024",
    SOURCE_NOTE,
)
save(fig, "charts/taxes_canton_par_type.png")

print("wrote charts/taxes_canton_par_type.png")
print("wrote charts/taxes_canton_par_type.csv")
