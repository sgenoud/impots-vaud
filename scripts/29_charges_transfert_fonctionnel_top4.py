"""Charges de transfert, by function, the 4 main categories only, per
inhabitant -- in CHF, and in units of the median salary -- 2014-2025.

A simpler companion to scripts/28_charges_transfert_fonctionnel.py: just
the 4 biggest functions by cumulative CHF over 2014-2024 -- Prévoyance
sociale, Santé, Formation, Finances et impôts -- as their own lines, no
"Autres" residual (unlike script 28, this one doesn't claim to sum to
the charges-de-transfert total; it's a focused look at the 4 largest
drivers, not a full decomposition). Same two units as
scripts/26_charges_transfert_trend.py and scripts/28, so all three
charts are directly comparable.

Output: charts/charges_transfert_fonctionnel_top4_median_salary_ratio.png
        charts/charges_transfert_fonctionnel_top4.csv (still has the
        CHF-per-inhabitant figures, just no chart of its own)
"""
import pandas as pd
from _chart_style import BLUE, AQUA, YELLOW, GREEN, new_figure, style_axes, plot_series, add_titles, save

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, « Charges de transfert par "
    "classification fonctionnelle » (détail du groupe de nature 36, "
    "2014-2025) ; population : Etat de Vaud / OFS.",
    "Les 4 fonctions retenues sont les plus importantes en valeur "
    "cumulée sur 2014-2024 (voir scripts/12_charges_transfert_fonctionnel.py) "
    "-- ce n'est pas une décomposition complète, contrairement au "
    "graphique à 6 lignes (scripts/28_charges_transfert_fonctionnel.py).",
]
SALARY_NOTE = (
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS)."
)

# key -> (label, color, source column), ranked by cumulative CHF 2014-2024
FUNCTIONS = {
    "prevoyance_sociale": ("Prévoyance sociale", BLUE, "charges_transfert_prevoyance_sociale_chf"),
    "sante": ("Santé", AQUA, "charges_transfert_sante_chf"),
    "formation": ("Formation", YELLOW, "charges_transfert_formation_chf"),
    "finances_impots": ("Finances et impôts", GREEN, "charges_transfert_finances_impots_chf"),
}

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[df["charges_transfert_fonc_total_chf"].notna()].copy()
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12

for key, (_, _, col) in FUNCTIONS.items():
    df[f"per_capita_{key}"] = df[col] / df["population_canton"]
    df[f"median_salary_ratio_{key}"] = df[f"per_capita_{key}"] / df["annual_median_salary_chf"]

derived_cols = ["year"] + [f"per_capita_{k}" for k in FUNCTIONS] + \
    [f"median_salary_ratio_{k}" for k in FUNCTIONS]
df[derived_cols].to_csv("charts/charges_transfert_fonctionnel_top4.csv", index=False)


def make_chart(value_prefix, y_fmt, title, subtitle, y_label, out_path, source):
    fig, ax = new_figure()
    plot_series(ax, df["year"].tolist(), [
        (label, color, df[f"{value_prefix}_{key}"].tolist())
        for key, (label, color, _) in FUNCTIONS.items()
    ])
    style_axes(ax, y_fmt)
    add_titles(fig, ax, title, subtitle, source)
    ax.set_ylabel(y_label, fontsize=9, color="#898781")
    save(fig, out_path)
    print(f"wrote {out_path}")


make_chart(
    "median_salary_ratio", lambda v, _: f"{v * 100:.2f}%",
    "Charges de transfert de l'Etat de Vaud, 4 principales fonctions, en salaires médians",
    "Prévoyance sociale, santé, formation et finances/impôts par habitant, "
    "exprimées en unités de salaire annuel médian vaudois (estimé), 2014-2025",
    "% d'un salaire annuel médian",
    "charts/charges_transfert_fonctionnel_top4_median_salary_ratio.png",
    [*SOURCE_NOTE, SALARY_NOTE],
)

print("wrote charts/charges_transfert_fonctionnel_top4.csv")
