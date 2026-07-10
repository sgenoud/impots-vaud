"""Where the rise in charges de transfert comes from: the same charges de
transfert (MCH2 nature group 36), broken down by functional
classification (health, education, social welfare, ...) instead of by
nature, per inhabitant -- in CHF, and in units of the median salary --
2014-2025.

Same two units as scripts/26_charges_transfert_trend.py, so the two
charts are directly comparable: this one just splits that single line
into where the money goes instead of what kind of expense it is. No
MCH1/MCH2 break needed -- functional classification is a MCH2-era
report with no MCH1 equivalent in this pipeline, so it's one unbroken
series.

5 named functions -- Prévoyance sociale, Santé, Formation, Trafic et
télécommunications, Finances et impôts -- cover about 95% of the total
cumulated over 2014-2024 (see scripts/12_charges_transfert_fonctionnel.py);
the rest (Economie publique, Culture/sport/loisirs/église, Protection de
l'environnement, Ordre et sécurité, Administration générale) is bucketed
into a 6th "Autres" residual, same pattern as
scripts/24_charges_main_categories.py. The residual is exact: computed
from this file's own TOTAL row (charges_transfert_fonc_total_chf) minus
the 5 named functions, not from charges_transfert_mch2_chf -- which lets
2025 (present here, not in the general charges report) work too.

Output: charts/charges_transfert_fonctionnel_median_salary_ratio.png
        charts/charges_transfert_fonctionnel.csv (still has the
        CHF-per-inhabitant figures, just no chart of its own)
"""
import pandas as pd
from _chart_style import (
    BLUE, AQUA, YELLOW, GREEN, VIOLET,
    new_figure, style_axes, plot_broken_series, add_titles, save,
)

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, « Charges de transfert par "
    "classification fonctionnelle » (détail du groupe de nature 36, "
    "2014-2025) ; population : Etat de Vaud / OFS.",
    "« Autres » regroupe Economie publique, Culture/sport/loisirs/église, "
    "Protection de l'environnement, Ordre et sécurité, et Administration "
    "générale -- environ 5% du total cumulé sur 2014-2024. 2025 est "
    "présent dans cette source mais pas encore dans le rapport général des "
    "charges par nature (scripts/11_charges_etat.py).",
]
SALARY_NOTE = (
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS)."
)

# key -> (label, color, source column)
FUNCTIONS = {
    "prevoyance_sociale": ("Prévoyance sociale", BLUE, "charges_transfert_prevoyance_sociale_chf"),
    "sante": ("Santé", AQUA, "charges_transfert_sante_chf"),
    "formation": ("Formation", YELLOW, "charges_transfert_formation_chf"),
    "trafic_telecom": ("Trafic et télécommunications", GREEN, "charges_transfert_trafic_telecom_chf"),
    "finances_impots": ("Finances et impôts", VIOLET, "charges_transfert_finances_impots_chf"),
}

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[df["charges_transfert_fonc_total_chf"].notna()].copy()
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12

named_chf = pd.DataFrame({key: df[col] for key, (_, _, col) in FUNCTIONS.items()})
named_chf["autres"] = df["charges_transfert_fonc_total_chf"] - named_chf.sum(axis=1)

for key in named_chf.columns:
    df[f"per_capita_{key}"] = named_chf[key] / df["population_canton"]
    df[f"median_salary_ratio_{key}"] = df[f"per_capita_{key}"] / df["annual_median_salary_chf"]

ALL_KEYS = [(k, label, color) for k, (label, color, _) in FUNCTIONS.items()]
ALL_KEYS.append(("autres", "Autres", "#898781"))

derived_cols = ["year"] + [f"per_capita_{k}" for k, _, _ in ALL_KEYS] + \
    [f"median_salary_ratio_{k}" for k, _, _ in ALL_KEYS]
df[derived_cols].to_csv("charts/charges_transfert_fonctionnel.csv", index=False)


def make_chart(value_prefix, y_fmt, title, subtitle, y_label, out_path, source):
    fig, ax = new_figure()
    years = df["year"].tolist()
    plot_broken_series(ax, [
        (label, color, [(years, df[f"{value_prefix}_{key}"].tolist())])
        for key, label, color in ALL_KEYS
    ])
    style_axes(ax, y_fmt)
    add_titles(fig, ax, title, subtitle, source)
    ax.set_ylabel(y_label, fontsize=9, color="#898781")
    save(fig, out_path)
    print(f"wrote {out_path}")


make_chart(
    "median_salary_ratio", lambda v, _: f"{v * 100:.2f}%",
    "Charges de transfert de l'Etat de Vaud, par fonction, en salaires médians",
    "Charges de transfert par habitant, par classification fonctionnelle, "
    "exprimées en unités de salaire annuel médian vaudois (estimé), "
    "2014-2025",
    "% d'un salaire annuel médian",
    "charts/charges_transfert_fonctionnel_median_salary_ratio.png",
    [*SOURCE_NOTE, SALARY_NOTE],
)

print("wrote charts/charges_transfert_fonctionnel.csv")
