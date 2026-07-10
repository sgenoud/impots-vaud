"""The state's 6 main charge categories, per inhabitant -- in CHF, and in
units of the median salary, 1993-2024.

Five of the nature-code groups (30 personnel, 31 biens et services, 33
amortissements, 36 transferts, 37 subventions à redistribuer) keep the
same code -- and roughly the same meaning -- across the MCH1 -> MCH2
accounting-standard switch, so each is plotted as one series with a
disconnected break at 2013 -> 2014 (see scripts/23_charges_charts.py
and README for why the break, not one continuous line, is the honest
way to show these). The first chart is CHF per inhabitant
(population_canton); the second divides that again by the median
annual Vaud salary (salaire_median_vaud_approx_chf x 12) to get a plain
ratio -- e.g. 0.02 means "worth 2% of one median annual salary" --
rather than a percentage.

The 6th line, "Autres", is a residual (total minus those 5), not a
single nature code: MCH1's remaining groups (32 intérêts, 34 parts et
contributions, 35 remboursements aux collectivités, 38 attributions aux
fonds, 39 imputations internes) and MCH2's remaining groups (34 charges
financières, 35 attributions aux fonds, 38 charges extraordinaires, 39
imputations internes) don't correspond to each other code-for-code --
e.g. MCH2's "38 Charges extraordinaires" has no real MCH1 equivalent --
so bucketing them into one "everything else" line is more honest than
pretending a 6th direct pairing exists. The residual is exact: each
period's 5 named groups + Autres sum to charges_totales_chf.

Output: charts/charges_main_categories_median_salary_ratio.png
        charts/charges_main_categories_per_capita.csv (still has the
        CHF-per-inhabitant figures, just no chart of its own)
"""
import pandas as pd
from _chart_style import (
    BLUE, AQUA, YELLOW, GREEN, VIOLET,
    new_figure, style_axes, plot_broken_series, add_titles, save,
)

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, charges par nature "
    "(« 5.2 Charges de fonctionnement par nature » 1993-2013 ; "
    "« 5.2 Charges compte de résultat par nature » 2014-2024) ; "
    "population : Etat de Vaud / OFS.",
    "Rupture 2013/2014 : changement de norme comptable (MCH1 -> MCH2), qui "
    "redéfinit le périmètre de plusieurs catégories ; les segments avant et "
    "après ne sont pas directement comparables. « Autres » est un résidu "
    "(non un code unique) et diffère donc aussi de nature entre les deux périodes.",
]
SALARY_NOTE = (
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS)."
)

# key -> (label, color, mch1 source column, mch2 source column)
CATEGORIES = {
    "transfert": ("Charges de transfert", BLUE,
                  "charges_aides_subventions_privees_mch1_chf", "charges_transfert_mch2_chf"),
    "personnel": ("Charges de personnel", AQUA,
                  "charges_personnel_mch1_chf", "charges_personnel_mch2_chf"),
    "biens_services": ("Biens et services", YELLOW,
                        "charges_biens_services_mch1_chf", "charges_biens_services_mch2_chf"),
    "subventions_redistribuer": ("Subventions à redistribuer", GREEN,
                                  "charges_subventions_redistribuees_mch1_chf",
                                  "charges_subventions_redistribuer_mch2_chf"),
    "amortissements": ("Amortissements", VIOLET,
                       "charges_amortissements_mch1_chf", "charges_amortissements_mch2_chf"),
}

df = pd.read_csv("output/vaud_taxes_master.csv")
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12


def build_period(df: pd.DataFrame, use_mch1: bool) -> pd.DataFrame:
    filter_col = CATEGORIES["personnel"][2 if use_mch1 else 3]
    sub = df[df[filter_col].notna()].copy()
    out = pd.DataFrame({"year": sub["year"], "norme": "mch1" if use_mch1 else "mch2"})

    named_chf = pd.DataFrame({
        key: sub[mch1_col if use_mch1 else mch2_col]
        for key, (_, _, mch1_col, mch2_col) in CATEGORIES.items()
    })
    named_chf["autres"] = sub["charges_totales_chf"] - named_chf.sum(axis=1)

    for key in named_chf.columns:
        per_capita = named_chf[key] / sub["population_canton"]
        out[f"per_capita_{key}"] = per_capita
        out[f"median_salary_ratio_{key}"] = per_capita / sub["annual_median_salary_chf"]
    return out


df1 = build_period(df, use_mch1=True)
df2 = build_period(df, use_mch1=False)

derived = pd.concat([df1, df2], ignore_index=True)
derived.to_csv("charts/charges_main_categories_per_capita.csv", index=False)

ALL_KEYS = [(k, label, color) for k, (label, color, _, _) in CATEGORIES.items()]
ALL_KEYS.append(("autres", "Autres", "#898781"))


def make_chart(value_prefix, y_fmt, title, subtitle, y_label, out_path, source):
    fig, ax = new_figure()
    series = [
        (label, color,
         [(df1["year"].tolist(), df1[f"{value_prefix}_{key}"].tolist()),
          (df2["year"].tolist(), df2[f"{value_prefix}_{key}"].tolist())])
        for key, label, color in ALL_KEYS
    ]
    plot_broken_series(ax, series)
    style_axes(ax, y_fmt)
    add_titles(fig, ax, title, subtitle, source)
    ax.set_ylabel(y_label, fontsize=9, color="#898781")
    save(fig, out_path)
    print(f"wrote {out_path}")


make_chart(
    "median_salary_ratio", lambda v, _: f"{v * 100:.1f}%",
    "Les 6 principales charges de l'Etat de Vaud, en salaires médians",
    "Charges de transfert, de personnel, biens et services, subventions à "
    "redistribuer, amortissements et autres par habitant, exprimées en "
    "unités de salaire annuel médian vaudois (estimé), 1993-2024",
    "% d'un salaire annuel médian",
    "charts/charges_main_categories_median_salary_ratio.png",
    [*SOURCE_NOTE, SALARY_NOTE],
)

print("wrote charts/charges_main_categories_per_capita.csv")
