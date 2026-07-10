"""Subsides cantonaux aux primes d'assurance-maladie, per inhabitant, in
units of the median salary, by beneficiary type, 1986-2024.

Same unit as the rest of the charges charts (scripts/23-30): CHF per
inhabitant (population_canton), divided again by the median annual Vaud
salary (salaire_median_vaud_approx_chf x 12) to get a plain ratio,
displayed as a percentage. No separate CHF-per-inhabitant chart, per
the same "median-salary units only" convention used since script 23 was
trimmed down (see README).

The 4 beneficiary-type columns (scripts/13_subsides_maladie.py) sum
exactly to the source's own total, so no "Autres" residual is needed --
same pattern as scripts/30_charges_transfert_prevoyance_detail.py. Two
of the 4 are complementary in time rather than overlapping: "Collectif
personnes âgées" was discontinued and "RI et assimilés / cas de
rigueur" introduced the same year (1996, when LAMal took effect) -- so
each is drawn as its own run via gap_segments, not interpolated across
the 1995/1996 boundary.

This is a longer, older series (1986-2024) than the functional
charges-de-transfert breakdown (2014-2025) -- a different source
(DGCS / Office vaudois de l'assurance-maladie) than the MCH2 nature/
functional reports, and not cross-checked against
charges_transfert_prevoyance_maladie_accident_chf (scripts/12), since
its scope (LAMal premium subsidies specifically) may differ from that
broader functional category.

Output: charts/subsides_maladie_median_salary_ratio.png
        charts/subsides_maladie_median_salary_ratio.csv
"""
import pandas as pd
from _chart_style import (
    BLUE, AQUA, YELLOW, GREEN,
    new_figure, style_axes, plot_broken_series, add_titles, save, gap_segments,
)

SOURCE_NOTE = [
    "Source : DGCS / Office vaudois de l'assurance-maladie, « Dépenses en "
    "francs pour les subsides aux primes d'assurance-maladie par type de "
    "bénéficiaires, Vaud, 1986-2024 » ; population : Etat de Vaud / OFS.",
    "« Collectif personnes âgées » a été supprimé et « RI et assimilés / "
    "cas de rigueur » introduit la même année (1996, entrée en vigueur de "
    "la LAMal) -- une rupture de trait signifie que la catégorie n'existe "
    "pas cette année-là, pas un montant nul.",
]
SALARY_NOTE = (
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS)."
)

# key -> (label, color, source column), ranked by cumulative CHF 1986-2024
CATEGORIES = {
    "partiels": ("Subsidiés partiels", BLUE, "subsides_maladie_partiels_chf"),
    "pc_avs_ai": ("Prestations complémentaires AVS/AI", AQUA, "subsides_maladie_pc_avs_ai_chf"),
    "ri_cas_rigueur": ("RI et cas de rigueur", YELLOW, "subsides_maladie_ri_cas_rigueur_chf"),
    "collectif_agees": ("Collectif personnes âgées", GREEN, "subsides_maladie_collectif_agees_chf"),
}

df = pd.read_csv("output/vaud_taxes_master.csv")
df = df[df["subsides_maladie_total_chf"].notna()].copy()
df["annual_median_salary_chf"] = df["salaire_median_vaud_approx_chf"] * 12

for key, (_, _, col) in CATEGORIES.items():
    df[f"per_capita_{key}"] = df[col] / df["population_canton"]
    df[f"median_salary_ratio_{key}"] = df[f"per_capita_{key}"] / df["annual_median_salary_chf"]

derived_cols = ["year"] + [f"per_capita_{k}" for k in CATEGORIES] + \
    [f"median_salary_ratio_{k}" for k in CATEGORIES]
df[derived_cols].to_csv("charts/subsides_maladie_median_salary_ratio.csv", index=False)

years = df["year"].tolist()
fig, ax = new_figure()
plot_broken_series(ax, [
    (label, color, gap_segments(years, df[f"median_salary_ratio_{key}"].tolist()))
    for key, (label, color, _) in CATEGORIES.items()
])
style_axes(ax, lambda v, _: f"{v * 100:.2f}%")
add_titles(
    fig, ax,
    "Subsides aux primes d'assurance-maladie, par type de bénéficiaire, en salaires médians",
    "Subsides cantonaux LAMal par habitant, par type de bénéficiaire, "
    "exprimés en unités de salaire annuel médian vaudois (estimé), 1986-2024",
    [*SOURCE_NOTE, SALARY_NOTE],
)
ax.set_ylabel("% d'un salaire annuel médian", fontsize=9, color="#898781")
save(fig, "charts/subsides_maladie_median_salary_ratio.png")

print("wrote charts/subsides_maladie_median_salary_ratio.png")
print("wrote charts/subsides_maladie_median_salary_ratio.csv")
