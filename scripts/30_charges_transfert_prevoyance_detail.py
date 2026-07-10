"""Prévoyance sociale (the main driver of the charges-de-transfert rise,
see scripts/28-29), broken down into its 6 functional sub-categories,
per inhabitant -- in CHF, and in units of the median salary -- 2014-2025.

51/52/53/54/55/57 (maladie-accident, invalidité, vieillesse-survivants,
famille-jeunesse, chômage, aide sociale-asile) are a complete partition
of code "5" in this source (56/58/59 don't exist) -- they sum almost
exactly to charges_transfert_prevoyance_sociale_chf (checked in
scripts/12_charges_transfert_fonctionnel.py), so unlike scripts/24 and
28, no "Autres" residual is needed here: all 6 lines are named.

Same two units as scripts/26/28/29, so all four charts are directly
comparable.

Output: charts/charges_transfert_prevoyance_detail_median_salary_ratio.png
        charts/charges_transfert_prevoyance_detail.csv (still has the
        CHF-per-inhabitant figures, just no chart of its own)
"""
import pandas as pd
from _chart_style import (
    BLUE, AQUA, YELLOW, GREEN, VIOLET, RED,
    new_figure, style_axes, plot_broken_series, add_titles, save,
)

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, « Charges de transfert par "
    "classification fonctionnelle » (détail des sous-fonctions 51/52/53/"
    "54/55/57 sous « 5 Prévoyance sociale », 2014-2025) ; population : "
    "Etat de Vaud / OFS.",
    "Les 6 sous-fonctions couvrent l'intégralité de la Prévoyance "
    "sociale (aucun résidu « Autres »).",
]
SALARY_NOTE = (
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS)."
)

# key -> (label, color, source column), ranked by cumulative CHF 2014-2024
SUBFUNCTIONS = {
    "aide_sociale_asile": ("Aide sociale et asile", BLUE, "charges_transfert_prevoyance_aide_sociale_asile_chf"),
    "maladie_accident": ("Maladie et accident", AQUA, "charges_transfert_prevoyance_maladie_accident_chf"),
    "invalidite": ("Invalidité", YELLOW, "charges_transfert_prevoyance_invalidite_chf"),
    "famille_jeunesse": ("Famille et jeunesse", GREEN, "charges_transfert_prevoyance_famille_jeunesse_chf"),
    "vieillesse_survivants": ("Vieillesse et survivants", VIOLET, "charges_transfert_prevoyance_vieillesse_survivants_chf"),
    "chomage": ("Chômage", RED, "charges_transfert_prevoyance_chomage_chf"),
}

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[df["charges_transfert_prevoyance_sociale_chf"].notna()].copy()
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12

for key, (_, _, col) in SUBFUNCTIONS.items():
    df[f"per_capita_{key}"] = df[col] / df["population_canton"]
    df[f"median_salary_ratio_{key}"] = df[f"per_capita_{key}"] / df["annual_median_salary_chf"]

derived_cols = ["year"] + [f"per_capita_{k}" for k in SUBFUNCTIONS] + \
    [f"median_salary_ratio_{k}" for k in SUBFUNCTIONS]
df[derived_cols].to_csv("charts/charges_transfert_prevoyance_detail.csv", index=False)


def make_chart(value_prefix, y_fmt, title, subtitle, y_label, out_path, source):
    fig, ax = new_figure()
    years = df["year"].tolist()
    plot_broken_series(ax, [
        (label, color, [(years, df[f"{value_prefix}_{key}"].tolist())])
        for key, (label, color, _) in SUBFUNCTIONS.items()
    ])
    style_axes(ax, y_fmt)
    add_titles(fig, ax, title, subtitle, source)
    ax.set_ylabel(y_label, fontsize=9, color="#898781")
    save(fig, out_path)
    print(f"wrote {out_path}")


make_chart(
    "median_salary_ratio", lambda v, _: f"{v * 100:.2f}%",
    "Prévoyance sociale de l'Etat de Vaud, par sous-fonction, en salaires médians",
    "Charges de transfert de prévoyance sociale par habitant, par "
    "sous-fonction, exprimées en unités de salaire annuel médian "
    "vaudois (estimé), 2014-2025",
    "% d'un salaire annuel médian",
    "charts/charges_transfert_prevoyance_detail_median_salary_ratio.png",
    [*SOURCE_NOTE, SALARY_NOTE],
)

print("wrote charts/charges_transfert_prevoyance_detail.csv")
