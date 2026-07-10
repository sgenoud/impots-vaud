"""Total subsides aux primes d'assurance-maladie, per inhabitant, in
units of the median salary, 1986-2024, with an OLS trend line fit over
2014-2024 (the same recent-decade window used for the charges-de-transfert
trend in scripts/26_charges_transfert_trend.py).

Simpler companion to scripts/31_subsides_maladie_chart.py: just
subsides_maladie_total_chf as a single line, no split by beneficiary
type. The full 1986-2024 line is still drawn for context, but the fit
(and its dashed line) only covers 2014-2024 -- recent years are where
the steepest rise happens (see script 31), so that's the trend worth
quantifying, not the whole 39-year span.

Slope significance (H0: slope = 0, i.e. no trend) is read off
scipy.stats.linregress's p-value with a 95% CI on the slope via the
t-distribution -- printed on the chart and to stdout.

Output: charts/subsides_maladie_total_median_salary_ratio.png
        charts/subsides_maladie_total_median_salary_ratio.csv
"""
import pandas as pd
from _chart_style import BLUE, INK_MUTED, new_figure, style_axes, plot_series, add_titles, save
from _stats import ols_fit

SOURCE_NOTE = [
    "Source : DGCS / Office vaudois de l'assurance-maladie, « Dépenses en "
    "francs pour les subsides aux primes d'assurance-maladie par type de "
    "bénéficiaires, Vaud, 1986-2024 » ; population : Etat de Vaud / OFS.",
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS).",
    "Régression sur 2014-2024 uniquement ; la ligne pleine couvre 1986-2024 pour contexte.",
]

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[df["subsides_maladie_total_chf"].notna()].copy()
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12
df["per_capita_chf"] = df["subsides_maladie_total_chf"] / df["population_canton"]
df["median_salary_ratio"] = df["per_capita_chf"] / df["annual_median_salary_chf"]

df_fit = df[df["year"] >= 2014].copy()
x = df_fit["year"].to_numpy()
y = df_fit["median_salary_ratio"].to_numpy()
fit, slope_lo, slope_hi, r_squared, verdict = ols_fit(x, y)
n = len(x)
df_fit["fit_median_salary_ratio"] = fit.intercept + fit.slope * df_fit["year"]

print(f"OLS 2014-2024 (n={n}): pente = {fit.slope * 100:.4f}%/an "
      f"(IC95% [{slope_lo * 100:.4f}%, {slope_hi * 100:.4f}%]), R² = {r_squared:.2f}, "
      f"p = {fit.pvalue:.4g} -> {verdict}")

df = df.merge(df_fit[["year", "fit_median_salary_ratio"]], on="year", how="left")
df[["year", "per_capita_chf", "median_salary_ratio", "fit_median_salary_ratio"]].to_csv(
    "charts/subsides_maladie_total_median_salary_ratio.csv", index=False
)

fig, ax = new_figure()
plot_series(ax, df["year"].tolist(), [
    ("Total subsides maladie", BLUE, df["median_salary_ratio"].tolist()),
])
ax.plot(
    df_fit["year"], df_fit["fit_median_salary_ratio"],
    color=INK_MUTED, linewidth=1.5, linestyle="--", zorder=2,
)
ax.text(
    df["year"].iloc[0], df["median_salary_ratio"].max(),
    f"régression 2014-2024 :\n+{fit.slope * 100:.4f}%/an "
    f"(IC95% [{slope_lo * 100:.4f}%, {slope_hi * 100:.4f}%])\n"
    f"R² = {r_squared:.2f}, p = {fit.pvalue:.4g}",
    color=INK_MUTED,
    fontsize=8.5,
    va="top",
    ha="left",
)
style_axes(ax, lambda v, _: f"{v * 100:.2f}%")
add_titles(
    fig, ax,
    "Total des subsides aux primes d'assurance-maladie, par habitant, en salaires médians",
    "Ensemble des subsides cantonaux LAMal par habitant, exprimés en "
    "unités de salaire annuel médian vaudois (estimé), et régression "
    "linéaire (MCO) sur 2014-2024, 1986-2024",
    SOURCE_NOTE,
)
ax.set_ylabel("% d'un salaire annuel médian", fontsize=9, color="#898781")
save(fig, "charts/subsides_maladie_total_median_salary_ratio.png")

print("wrote charts/subsides_maladie_total_median_salary_ratio.png")
print("wrote charts/subsides_maladie_total_median_salary_ratio.csv")
