"""Charges de transfert, per inhabitant -- in CHF, and in units of the
median salary -- with an OLS trend line fitted over the MCH2 period
(2014-2024): is the post-MCH2 level stable, or is there a real trend?

The pre-2014 segment (MCH1's "Aides individuelles, subventions à
institutions privées") is drawn for context only, same as the other
charges charts -- it's a different definition (see
scripts/24_charges_main_categories.py), so each regression is fit
exclusively on the 11 MCH2 points (2014-2024), where "charges de
transfert" is one consistently defined nature-group code.

Each fit is ordinary least squares, year vs. the chart's unit. Slope
significance (H0: slope = 0, i.e. no trend) is read off
scipy.stats.linregress's p-value with a 95% CI on the slope via the
t-distribution (n=11, df=9) -- printed on the chart and to stdout, not
just left in the source. The two units can disagree about "stability":
per-capita CHF mostly tracks the whole budget's growth, while the
median-salary-ratio also nets out wage growth, so a flat per-capita
trend is not automatically a flat salary-ratio trend or vice versa --
each is fit independently, not derived from the other.

Only the median-salary-ratio trend gets a chart; the CHF-per-inhabitant
regression is still computed and printed to stdout (and kept in the
CSV) since the two numbers are meant to be quoted together -- see
README -- it just doesn't get its own PNG.

Output: charts/charges_transfert_trend_median_salary_ratio.png
        charts/charges_transfert_trend.csv
"""
import pandas as pd
from _chart_style import BLUE, INK_MUTED, new_figure, style_axes, plot_broken_series, add_titles, save
from _stats import ols_fit

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, charges par nature "
    "(« 5.2 Charges de fonctionnement par nature » 1993-2013 ; "
    "« 5.2 Charges compte de résultat par nature » 2014-2024) ; "
    "population : Etat de Vaud / OFS.",
    "Rupture 2013/2014 : changement de norme comptable (MCH1 -> MCH2) ; le "
    "segment 1993-2013 (« Aides individuelles, subventions à institutions "
    "privées ») est fourni pour contexte seulement, la régression ne porte "
    "que sur 2014-2024.",
]
SALARY_NOTE = (
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS)."
)

df = pd.read_csv("output/vaud_taxes_master.csv")
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12
df["per_capita_transfert_mch1"] = (
    df["charges_aides_subventions_privees_mch1_chf"] / df["population_canton"]
)
df["per_capita_transfert_mch2"] = df["charges_transfert_mch2_chf"] / df["population_canton"]
df["median_salary_ratio_transfert_mch1"] = (
    df["per_capita_transfert_mch1"] / df["annual_median_salary_chf"]
)
df["median_salary_ratio_transfert_mch2"] = (
    df["per_capita_transfert_mch2"] / df["annual_median_salary_chf"]
)

df1 = df[df["per_capita_transfert_mch1"].notna()].copy()
df2 = df[df["per_capita_transfert_mch2"].notna()].copy()


def fit_trend(col):
    x = df2["year"].to_numpy()
    y = df2[col].to_numpy()
    fit, slope_lo, slope_hi, r_squared, verdict = ols_fit(x, y)
    df2[f"fit_{col}"] = fit.intercept + fit.slope * df2["year"]
    return fit, slope_lo, slope_hi, r_squared, verdict


def report_trend(col, fmt_slope):
    fit, slope_lo, slope_hi, r_squared, verdict = fit_trend(col)
    n = len(df2)
    print(f"[{col}] OLS 2014-2024 (n={n}): pente = {fmt_slope(fit.slope)}/an "
          f"(IC95% [{fmt_slope(slope_lo)}, {fmt_slope(slope_hi)}]), R² = {r_squared:.2f}, "
          f"p = {fit.pvalue:.4f} -> {verdict}")
    return fit, slope_lo, slope_hi, r_squared


def make_chart(col, fmt_slope, y_fmt, title, subtitle, y_label, out_path, source, annotate_offset):
    fit, slope_lo, slope_hi, r_squared = report_trend(col, fmt_slope)

    fig, ax = new_figure()
    plot_broken_series(ax, [
        ("Charges de transfert", BLUE, [
            (df1["year"].tolist(), df1[col.replace("mch2", "mch1")].tolist()),
            (df2["year"].tolist(), df2[col].tolist()),
        ]),
    ])
    ax.plot(
        df2["year"], df2[f"fit_{col}"],
        color=INK_MUTED, linewidth=1.5, linestyle="--", zorder=2,
    )
    ax.annotate(
        f"régression 2014-2024 :\n+{fmt_slope(fit.slope)}/an "
        f"(IC95% [{fmt_slope(slope_lo)}, {fmt_slope(slope_hi)}])\n"
        f"R² = {r_squared:.2f}, p = {fit.pvalue:.4f}",
        xy=(df2["year"].iloc[3], df2[f"fit_{col}"].iloc[3]),
        xytext=(0, annotate_offset),
        textcoords="offset points",
        color=INK_MUTED,
        fontsize=8.5,
        va="top",
    )

    style_axes(ax, y_fmt)
    add_titles(fig, ax, title, subtitle, source)
    ax.set_ylabel(y_label, fontsize=9, color="#898781")
    save(fig, out_path)
    print(f"wrote {out_path}")


report_trend("per_capita_transfert_mch2", lambda v: f"{v:,.0f} CHF".replace(",", "’"))
make_chart(
    "median_salary_ratio_transfert_mch2",
    lambda v: f"{v * 100:.3f}%",
    lambda v, _: f"{v * 100:.1f}%",
    "Charges de transfert de l'Etat de Vaud, en salaires médians, avec droite de régression",
    "Charges de transfert par habitant, exprimées en unités de salaire annuel "
    "médian vaudois (estimé), et régression linéaire (MCO) sur la période "
    "MCH2 (2014-2024), 1993-2024",
    "% d'un salaire annuel médian",
    "charts/charges_transfert_trend_median_salary_ratio.png",
    [*SOURCE_NOTE, SALARY_NOTE],
    annotate_offset=-55,
)

pd.concat([
    df1[["year", "per_capita_transfert_mch1", "median_salary_ratio_transfert_mch1"]],
    df2[[
        "year", "per_capita_transfert_mch2", "median_salary_ratio_transfert_mch2",
        "fit_per_capita_transfert_mch2", "fit_median_salary_ratio_transfert_mch2",
    ]],
], axis=0).to_csv("charts/charges_transfert_trend.csv", index=False)

print("wrote charts/charges_transfert_trend.csv")
