"""Charges de personnel, per inhabitant -- in CHF, and in units of the
median salary, 1993-2024.

Plots charges_personnel_mch1_chf (1993-2013) and charges_personnel_mch2_chf
(2014-2024) from output/vaud_taxes_master.csv, divided by population_canton
to get CHF per inhabitant, and that figure divided again by the median
annual Vaud salary (salaire_median_vaud_approx_chf x 12) to get a plain
ratio -- e.g. 0.04 means "the personnel charge per inhabitant is worth
4% of one median annual salary" -- rather than a percentage. Each is
drawn as two separate line segments -- not connected across 2013 ->
2014, since the accounting-standard switch (MCH1 -> MCH2) redefines
what the "personnel" group includes (see README: the group's raw CHF
value itself drops at the boundary even though total charges keep
rising smoothly, evidence of reclassification rather than a real
one-year cut). Both segments share one color: it's the same underlying
question ("how much does staff cost per inhabitant"), but the break
makes clear the two halves aren't one measured series.

Output: charts/charges_personnel_median_salary_ratio.png
        charts/charges_personnel_per_capita.csv (still has the
        CHF-per-inhabitant figures, just no chart of its own)
"""
import pandas as pd
from _chart_style import BLUE, new_figure, style_axes, plot_series, add_titles, save

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, charges par nature "
    "(« 5.2 Charges de fonctionnement par nature » 1993-2013 ; "
    "« 5.2 Charges compte de résultat par nature » 2014-2024) ; "
    "population : Etat de Vaud / OFS.",
    "Rupture 2013/2014 : changement de norme comptable (MCH1 -> MCH2), "
    "qui redéfinit le périmètre du groupe « personnel » ; "
    "les deux segments ne sont pas directement comparables.",
]
SALARY_NOTE = (
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS)."
)

df = pd.read_csv("output/vaud_taxes_master.csv")
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12

for norme in ("mch1", "mch2"):
    col = f"charges_personnel_{norme}_chf"
    per_capita_col = f"charges_personnel_per_capita_{norme}_chf"
    df[per_capita_col] = df[col] / df["population_canton"]
    df[f"charges_personnel_median_salary_ratio_{norme}"] = (
        df[per_capita_col] / df["annual_median_salary_chf"]
    )

derived_cols = [
    "year",
    "charges_personnel_per_capita_mch1_chf",
    "charges_personnel_per_capita_mch2_chf",
    "charges_personnel_median_salary_ratio_mch1",
    "charges_personnel_median_salary_ratio_mch2",
]
df[derived_cols].to_csv("charts/charges_personnel_per_capita.csv", index=False)

df_mch1 = df[df["charges_personnel_mch1_chf"].notna()]
df_mch2 = df[df["charges_personnel_mch2_chf"].notna()]

# --- in units of the median annual Vaud salary ---
fig, ax = new_figure()
plot_series(ax, df_mch1["year"].tolist(), [
    ("Personnel (1993-2013, MCH1)", BLUE, df_mch1["charges_personnel_median_salary_ratio_mch1"].tolist()),
])
plot_series(ax, df_mch2["year"].tolist(), [
    ("Personnel (2014-2024, MCH2)", BLUE, df_mch2["charges_personnel_median_salary_ratio_mch2"].tolist()),
])
style_axes(ax, lambda v, _: f"{v * 100:.1f}%")
add_titles(
    fig, ax,
    "Charges de personnel de l'Etat de Vaud, en salaires médians",
    "Charges de personnel par habitant, exprimées en unités de salaire annuel médian vaudois (estimé), 1993-2024",
    [*SOURCE_NOTE, SALARY_NOTE],
)
ax.set_ylabel("% d'un salaire annuel médian", fontsize=9, color="#898781")
save(fig, "charts/charges_personnel_median_salary_ratio.png")

print("wrote charts/charges_personnel_median_salary_ratio.png")
print("wrote charts/charges_personnel_per_capita.csv")
