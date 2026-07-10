"""Drilling into "Autres" (scripts/24_charges_main_categories.py): the 6
biggest individual line items behind it, per inhabitant -- in CHF, and
in units of the median salary, MCH2 only (2014-2024).

"Autres" there is a residual of 4 nature-groups (34 charges financières,
35 attributions aux fonds, 38 charges extraordinaires, 39 imputations
internes). This script reads the raw source file directly (rather than
output/vaud_taxes_master.csv, which only carries group-level totals) to
get down to the finest level it publishes -- individual "Gr 4" line
items -- and picks the 6 with the largest cumulative |value| over
2014-2024. The first chart is CHF per inhabitant (population_canton);
the second divides that again by the median annual Vaud salary
(salaire_median_vaud_approx_chf x 12) to get a plain ratio rather than a
percentage. Several of the 6 are one-off/irregular by nature (e.g. an
"attribution" booked only in some years), so each is plotted as its own
set of disconnected runs rather than one interpolated line -- a missing
year means the source reports nothing that year, not zero.

No MCH1 side: these are MCH2 (2014-2024) nature codes with no
established MCH1 correspondence (that's exactly why they end up in the
residual rather than one of the 5 named categories in chart 24).

Output: charts/charges_autres_detail_median_salary_ratio.png
        charts/charges_autres_detail_per_capita.csv (still has the
        CHF-per-inhabitant figures, just no chart of its own)
"""
import pandas as pd
from _chart_style import (
    BLUE, AQUA, YELLOW, GREEN, VIOLET, RED,
    new_figure, style_axes, plot_broken_series, add_titles, save, gap_segments,
)

SRC = "fichiers/5.2 Charges compte de résultat par nature (4p), en francs.xlsx"
HEADER_ROW = 3

SOURCE_NOTE = [
    "Source : Etat de Vaud, Compte d'Etat, « 5.2 Charges compte de résultat "
    "par nature », lignes de détail (niveau « Gr 4 »), 2014-2024 ; "
    "population : Etat de Vaud / OFS.",
    "Les 6 lignes retenues sont celles à la plus grande valeur absolue "
    "cumulée sur 2014-2024, parmi les groupes 34/35/38/39 (le résidu "
    "« Autres » du graphique précédent). Une rupture de trait signifie "
    "qu'aucun montant n'est publié cette année-là pour cette ligne, pas "
    "un montant nul.",
]
SALARY_NOTE = (
    "Salaire : OFS, Enquête suisse sur la structure des salaires ; années "
    "intercalées à l'aide de l'indice suisse des salaires (OFS)."
)

# leaf code -> (short chart label, color). Full official names are long
# (e.g. 3893's is "Attributions aux préfinancements du capital propre");
# shortened here so the direct end-of-line labels fit in the chart margin
# -- see the CSV or the source file for the exact wording.
LEAVES = {
    3898: ("3898 Autres capitaux propres", BLUE),
    3893: ("3893 Préfinancements (capital propre)", AQUA),
    3511: ("3511 Fonds du capital propre", YELLOW),
    3830: ("3830 Amort. suppl. bâtiments", GREEN),
    3510: ("3510 Financements spéciaux", VIOLET),
    3499: ("3499 Autres charges financières", RED),
}

df_raw = pd.read_excel(SRC, sheet_name=0, header=None)
year_cols = {}
for col in df_raw.columns:
    year = df_raw.iat[HEADER_ROW, col]
    if isinstance(year, (int, float)) and not pd.isna(year) and 2014 <= year <= 2024:
        year_cols[int(year)] = col
years = sorted(year_cols)

master = pd.read_csv("output/vaud_taxes_master.csv").set_index("year")
population = master["population_canton"]
annual_median_salary = master["salaire_median_vaud_approx_chf"] * 12

records_per_capita = {"year": years}
records_salary_ratio = {"year": years}
for leaf_code, (label, _) in LEAVES.items():
    row = df_raw[df_raw[4] == leaf_code]
    values = [row.iat[0, year_cols[y]] for y in years]
    per_capita_values = [
        v / population[y] if pd.notna(v) else None for y, v in zip(years, values)
    ]
    records_per_capita[str(leaf_code)] = per_capita_values
    records_salary_ratio[str(leaf_code)] = [
        pc / annual_median_salary[y] if pc is not None else None
        for y, pc in zip(years, per_capita_values)
    ]

derived_per_capita = pd.DataFrame(records_per_capita)
derived_salary_ratio = pd.DataFrame(records_salary_ratio)
derived_per_capita.to_csv("charts/charges_autres_detail_per_capita.csv", index=False)


def make_chart(derived, y_fmt, title, subtitle, y_label, out_path, source):
    fig, ax = new_figure()
    series = [
        (label, color, gap_segments(years, derived[str(leaf_code)].tolist()))
        for leaf_code, (label, color) in LEAVES.items()
    ]
    plot_broken_series(ax, series)
    style_axes(ax, y_fmt)
    add_titles(fig, ax, title, subtitle, source)
    ax.set_ylabel(y_label, fontsize=9, color="#898781")
    save(fig, out_path)
    print(f"wrote {out_path}")


make_chart(
    derived_salary_ratio, lambda v, _: f"{v * 100:.2f}%",
    "A l'intérieur des « Autres » charges : le détail des 6 plus grosses lignes",
    "Les 6 lignes de détail (compte par nature) les plus importantes dans le "
    "résidu « Autres », par habitant, exprimées en unités de salaire annuel "
    "médian vaudois (estimé), 2014-2024",
    "% d'un salaire annuel médian",
    "charts/charges_autres_detail_median_salary_ratio.png",
    [*SOURCE_NOTE, SALARY_NOTE],
)

print("wrote charts/charges_autres_detail_per_capita.csv")
