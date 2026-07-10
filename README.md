# Impôts Vaud — data pipeline

Turns the raw files in `fichiers/` into one tidy CSV for analysis:
`output/vaud_taxes_master.csv`, one row per year, 1981-2025.

## Running it

Requires [uv](https://docs.astral.sh/uv/) (no manual venv/pip setup needed)
and [just](https://github.com/casey/just) as the command runner:

```sh
just         # list all recipes
just all     # extraction -> master table -> every chart
```

`just --list` (or plain `just`) shows every recipe with a one-line
description. The pipeline is staged, and each stage is its own recipe
that depends on the one before it — running a later recipe pulls in
whatever it needs, and `just` runs each shared dependency only once
per invocation:

- `just extract` — runs every `scripts/0N_*.py`/`1N_*.py` extraction
  script (raw file -> tidy `clean/<name>.csv`, always with a `year`
  column).
- `just master` — (depends on `extract`) runs
  `scripts/20_build_master.py`, which outer-joins every `clean/*.csv`
  on `year` into `output/vaud_taxes_master.csv`.
- `just charts` — (depends on `master`) runs `scripts/21_charts.py`.
- `just charts-vevey` — (depends on `master`) runs
  `scripts/22_charts_vevey.py`.
- `just charts-charges` — (depends on `master`) runs
  `scripts/23_charges_charts.py`.
- `just charts-charges-main` — (depends on `master`) runs
  `scripts/24_charges_main_categories.py`.
- `just charts-charges-autres` — (depends on `master`) runs
  `scripts/25_charges_autres_detail.py`.
- `just charts-charges-transfert-trend` — (depends on `master`) runs
  `scripts/26_charges_transfert_trend.py`.
- `just charts-charges-totales` — (depends on `master`) runs
  `scripts/27_charges_totales_median_salary.py`.
- `just charts-charges-transfert-fonctionnel` — (depends on `master`)
  runs `scripts/28_charges_transfert_fonctionnel.py`.
- `just charts-charges-transfert-fonctionnel-top4` — (depends on
  `master`) runs `scripts/29_charges_transfert_fonctionnel_top4.py`.
- `just charts-charges-transfert-prevoyance` — (depends on `master`)
  runs `scripts/30_charges_transfert_prevoyance_detail.py`.
- `just charts-subsides-maladie` — (depends on `master`) runs
  `scripts/31_subsides_maladie_chart.py`.
- `just charts-subsides-maladie-total` — (depends on `master`) runs
  `scripts/32_subsides_maladie_total.py`.
- `just all` — (depends on `charts`, `charts-vevey`, `charts-charges`,
  `charts-charges-main`, `charts-charges-autres`,
  `charts-charges-transfert-trend`, `charts-charges-totales`,
  `charts-charges-transfert-fonctionnel`,
  `charts-charges-transfert-fonctionnel-top4`,
  `charts-charges-transfert-prevoyance`, `charts-subsides-maladie` and
  `charts-subsides-maladie-total`) builds everything.
- `just run <script>` — run any single script directly, e.g.
  `just run 02_taxes_canton.py`.
- `just clean` — remove every generated file (`clean/`, `output/`,
  `charts/`) for a from-scratch rebuild.

## Sources and columns

| Column | Source file | Sheet | Years | Unit |
|---|---|---|---|---|
| `population_canton` | `Chiffres-cles_Population_depuis-1981.xls` | Feuil1 | 1981-2025 | headcount |
| `taxes_canton_chf` | `T18.02.04.xlsx` | `1990-2013` + `2013 et suite` | 1990-2024 | CHF (raw, converted from millions) |
| `taxes_communes_chf` | `a) Ensemble des communes.xlsx` | — | 1990-2024 | CHF (all VD communes combined) |
| `taxes_vevey_chf` | `b) Par communes.xlsx` | — | 1990-2024 | CHF (Vevey only, pre-filtered in source) |
| `pib_nominal_chf` | `PIB-VD_nominal_depuis_1997.xlsx` | — | 1997-2025 | CHF (raw, converted from millions) |
| `pib_reel_chf` | `PIB-VD_reel_depuis_1997.xlsx` | — | 1997-2025 | CHF, chained to prior-year prices, ref. year 2025 |
| `charges_totales_chf` | `5.2 Charges de fonctionnement...xlsx` (1993-2013) + `5.2 Charges compte de résultat...xlsx` (2014-2024) | — | 1993-2024 | CHF, one continuous series across the MCH1->MCH2 accounting-standard switch |
| `charges_<nature>_mch1_chf` / `_mch2_chf` | same two files as above | — | 1993-2013 / 2014-2024 | CHF, by-nature group subtotals (personnel, biens et services, ...); **not comparable across the mch1/mch2 split**, see below |
| `charges_transfert_<fonction>_chf` / `_fonc_total_chf` | `Charges_de_transfert_par_classification_fonctionnelle.xlsx` | — | 2014-2025 | CHF (raw, converted from thousands); charges de transfert (nature group 36) broken down by function (santé, formation, ...) instead of by nature |
| `charges_transfert_prevoyance_<sous-fonction>_chf` | same file, sub-codes 51/52/53/54/55/57 | — | 2014-2025 | CHF (raw, converted from thousands); Prévoyance sociale broken down further, into a complete partition (no residual) |
| `subsides_maladie_<type>_chf` / `_total_chf` | `subsides-francs.xlsx` | Serie | 1986-2024 | CHF (already raw francs in source); subsides LAMal by beneficiary type, a complete partition (no residual) |
| `cpi_dec1982_base100` | `T05.01.01.xlsx` | `Base Déc_1982` | 1977-2025 | index, Dec 1982 = 100 |
| `wage_index_ch_nominal` / `_real` | `ts-x-03.04.03.02.01.csv` | — | 1942-2020 | index points, **Swiss national**, not Vaud |
| `population_vevey` | `px-x-0102020000_201.px` (1981-2024) + `2. Population résidante permanente...2017-2025.xlsx` (2025 only) | — | 1981-2025 | headcount |
| `salaire_median_vaud_chf` | `1_salaire_caracteristique.xlsx` | `Tous_secteurs` | 2012-2024, biennial | CHF/month, **median** (not mean), full-time standardized |
| `salaire_median_vaud_approx_chf` / `_method` | derived: `salaire_median_vaud_chf` + `wage_index_ch_nominal` | — | 1981-2025, annual | CHF/month, **modeled**, see below |

All monetary columns share one unit (raw CHF, not millions) so they're
directly comparable/summable.

## Known gaps (as of 2026-07-02)

- **Mean salary**: no source gives a true Vaud *mean* salary. Two real
  proxies are included: `salaire_median_vaud_chf` (real Vaud data, but
  *median*, all-sectors, and only every 2 years since it comes from
  the biennial Swiss salary structure survey) and
  `wage_index_ch_nominal`/`_real` (Swiss *national* index points, not
  CHF, annual 1942-2020). Neither alone is a strict "mean salary for
  the canton" — treat them as the closest available approximations.

  `salaire_median_vaud_approx_chf` (built by
  `scripts/10_salaire_median_vaud_approx.py`) combines the two into one
  annual 1981-2025 series: real Vaud values are kept as-is at the 7
  anchor years, gaps between anchors are filled by geometric
  interpolation shaped by the CH wage index's actual year-to-year
  moves (or plain geometric interpolation where the index doesn't
  cover the gap, e.g. 2021/2023), 1981-2011 is extrapolated backward
  from the 2012 anchor using the CH index's level in each year, and
  2025 is extrapolated forward from the 2022-2024 trend (the CH index
  stops in 2020). The `salaire_median_vaud_approx_method` column
  records which of these four techniques produced each value — filter
  to `method == "actual"` to get only the real data points back out.
  This assumes Vaud salaries broadly track the national index's
  shape, which is a modeling assumption, not a measurement.
- The master table spans **1981-2025** (the union of what's
  available), so most columns have leading/trailing blanks outside
  their own source's coverage — e.g. taxes are blank before 1990, GDP
  before 1997, salary before 2012 and in odd years.
- GDP forecast years 2026-2027 (present in the real-GDP source,
  marked `*`) are dropped by the master build since no other series
  reaches that far.
- **Charges by nature (`charges_<nature>_mch1_chf` / `_mch2_chf`)**: the
  canton switched accounting standards (MCH1 -> MCH2) between the 2013
  and 2014 reports, and the new standard redefines what the `30`-`39`
  nature-group codes mean -- e.g. MCH1's `32 Intérêts passifs` is
  folded into MCH2's `34 Charges financières`, and MCH1's `34`/`35`/`36`
  transfer/subsidy categories are consolidated into one MCH2
  `36 Charges de transfert`. Only the grand total
  (`charges_totales_chf`) is a safe continuous series across the
  switch (CHF 9.27bn in 2013 -> 9.52bn in 2014, a plausible one-year
  step); the group columns are kept as two separate, differently-named
  sets, each populated only for its own period -- do not compare a
  `_mch1` column against the `_mch2` column of the same group number.
- `population_vevey`: the two source years that overlap (2017-2024)
  differ by a handful of people between the `.px` file and the annual
  commune file, most likely a data-vintage/revision difference; the
  `.px` series is used wherever it's available and the xlsx only fills
  in 2025 (the one year the `.px` file doesn't cover).
- `T01.02.03.xlsx` (commune-to-agglomeration mapping) and
  `T22.01.02.xlsx` (population snapshots at 1950/1980/2025 only) were
  also supplied but aren't used: the former has no population figures,
  and the latter's single 2025 snapshot is redundant with the annual
  file already used for `population_vevey`.

To add a new source (e.g. a real Vaud mean-salary series later): drop
a new extraction script (numbered anywhere in the 01-19 range, e.g.
`scripts/11_*.py`) that writes `clean/<name>.csv` with a `year`
column, then run `just master`. No other script needs editing — the
master build auto-discovers every `clean/*.csv`, and `just extract`'s
glob (`scripts/[0-1][0-9]_*.py`) picks up any script numbered 01-19
automatically. Numbers are grouped by stage: 01-19 extraction (raw
file -> `clean/*.csv`), 20 merge (`clean/*.csv` -> master), 21+
downstream/reporting (master -> charts, etc.) — keep new scripts
inside the right band and wire a new `just` recipe for a new
downstream stage the same way `charts`/`charts-vevey` are wired.

## Charts

None of these charts plot raw CHF-per-inhabitant anymore — that unit
was dropped from every chart (per user request) in favor of the
median-salary-ratio framing, which nets out both population and wage
growth. The CHF-per-inhabitant figures aren't gone from the data,
though: every script still computes them and keeps them in its `.csv`
output (e.g. `charges_personnel_per_capita_mch2_chf`), they just don't
get a chart of their own. `scripts/26_charges_transfert_trend.py` even
still prints the CHF-per-inhabitant regression to stdout — see its
entry below — since that number is part of the stability story, even
without a PNG.

`scripts/21_charts.py` builds two PNGs plus the numbers behind them,
all in `charts/`:

- `taxes_per_capita_pct_median_salary.png` — cantonal tax, all-communes
  tax, and the two combined, per inhabitant (`taxes_*_chf /
  population_canton`), expressed as a percentage of one median annual
  Vaud salary (`salaire_median_vaud_approx_chf x 12`), i.e. how many
  median annual salaries the per-inhabitant tax bill is worth. Since
  this leans on the *approximated* salary series, most of its
  year-to-year shape before 2012 and between anchors is modeled, not
  measured — see the gap note above.
- `taxes_per_capita_pct_pib.png` — tax revenue as a percentage of real
  GDP (`taxes_*_chf / pib_reel_chf`, chained to prior-year prices,
  ref. year 2025). This chart isn't per capita at all — population
  cancels out of `(taxes/pop) / (pib/pop)`, so revenue-over-GDP is the
  same ratio computed directly from the totals. Only 1997-2024, since
  GDP starts in 1997.
- `taxes_per_capita.csv` — the derived per-capita, per-salary, and
  per-PIB figures behind both charts (including plain CHF per
  inhabitant, which has no chart of its own), for inspection or
  further analysis.

The salary-share chart is restricted to 1990-2024 (where both tax
series exist); the PIB-share chart to 1997-2024 (where GDP also
exists). Styling follows the project's dataviz skill: a validated
categorical palette (`scripts/_chart_style.py`), thin lines, recessive
gridlines, and direct end-of-line labels.

`scripts/22_charts_vevey.py` builds the same salary-share chart for
Vevey alone (a single series, since there's no canton/communes split
at commune level): `taxes_vevey_per_capita_pct_median_salary.png` and
`taxes_vevey_per_capita.csv`. Same 1990-2024 restriction (where
`taxes_vevey_chf` exists) and same salary caveat — plus note this
compares a commune-level tax to a canton-level salary, since no
Vevey-specific salary data exists.

The charges scripts below (23-30) all use the same **ratio to the
median salary** — CHF per inhabitant (`population_canton`) divided
again by one median annual Vaud salary
(`salaire_median_vaud_approx_chf x 12`) — rather than "% of total
charges". The underlying data and the `.csv` columns
(`*_median_salary_ratio_*`) stay a plain 0-1 ratio (e.g. `0.057`), but
every chart's axis and any on-chart regression stats display it
multiplied by 100, as a percentage (`5.7%`) — easier to read at a
glance than a bare decimal.

`scripts/23_charges_charts.py` builds
`charges_personnel_median_salary_ratio.png` (+ its `.csv`): charges de
personnel, 1993-2024. Plotted as **two disconnected line segments**
(1993-2013 and 2014-2024) rather than one continuous line, because
that's exactly where the MCH1 -> MCH2 accounting-standard switch falls
— see the "Known gaps" note above on why the `_mch1`/`_mch2` group
columns aren't comparable. Same color both sides (same question, "how
much does staff cost per inhabitant"), but the visual break is the
point: it flags that the drop across 2013/2014 is a reclassification
artifact, not a real one-year change.

`scripts/24_charges_main_categories.py` builds
`charges_main_categories_median_salary_ratio.png` (+ its `.csv`): the
same break-at-2013/2014 treatment, generalized to the 6 largest charge
categories at once — personnel, biens et services, amortissements,
charges de transfert and subventions à redistribuer (each a
`_mch1`/`_mch2` pair sharing the same nature-group code both sides),
plus a 6th line, **Autres**, which is a residual (`charges_totales_chf`
minus the other 5) rather than a single nature code, since the
remaining groups don't correspond to each other across the standard
switch either (e.g. MCH2's `38 Charges extraordinaires` has no real
MCH1 equivalent). Labels that would otherwise land on top of each
other (several categories sit within a couple of points of one another
by 2024) are nudged apart vertically by
`_chart_style.plot_broken_series`, which both this script and
`23_charges_charts.py` share.

`scripts/25_charges_autres_detail.py` drills into that "Autres"
residual, MCH2 only (2014-2024):
`charges_autres_detail_median_salary_ratio.png` (+ its `.csv`) plots
the 6 individual line items (the finest level the source publishes,
its "Gr 4" rows) with the largest cumulative |value| over 2014-2024,
among the four groups that make up "Autres" (34 charges financières,
35 attributions aux fonds, 38 charges extraordinaires, 39 imputations
internes). Unlike the other charts, this one reads the raw source xlsx
directly instead of `output/vaud_taxes_master.csv`, since the master
table only carries group-level totals, not individual line items.
Several of the 6 are one-off/irregular (an "attribution" some years,
absent others), so each is drawn as its own disconnected runs via
`_chart_style.gap_segments` — a gap means the source reports nothing
that year, not zero.

`scripts/26_charges_transfert_trend.py` builds
`charges_transfert_trend_median_salary_ratio.png` (+ its `.csv`):
charges de transfert per inhabitant, 1993-2024, with an OLS trend line
(`scipy.stats.linregress`) fit only on the 11 MCH2 points (2014-2024) —
the pre-2014 segment is context only, same reasoning as the other
break-treated charts. The fitted slope, its 95% CI, R² and p-value are
annotated on the chart and printed to stdout — and the equivalent
CHF-per-inhabitant regression is *also* printed to stdout (and kept in
the `.csv`), even though it no longer gets a chart. As of the last run,
both units show a statistically real upward trend, not stability:
**+153 CHF/inhabitant/year** (95% CI [95, 211], R² = 0.80, p = 0.0002)
in CHF, and **+0.106 percentage points/year** of one median salary (95%
CI [0.034, 0.178], R² = 0.55, p = 0.0087) — weaker (R² is smaller) but
still significant at 5%, meaning charges de transfert are growing
faster than the median salary too, not just faster than
inflation/population. Re-run the same regression on the *share of
total charges* instead (`charges_transfert_mch2_chf /
charges_totales_chf`, not built into any script here) and the slope is
tiny and not significant (p ≈ 0.37) — so relative to the rest of the
budget specifically (as opposed to relative to inhabitants or
salaries), charges de transfert have been roughly stable. Which of
these is "the" stability question depends on what's being asked; all
three numbers are worth quoting together.

`scripts/27_charges_totales_median_salary.py` builds
`charges_totales_median_salary_ratio.png` (+ its `.csv`): total charges
per inhabitant, in median-salary-ratio units, 1993-2024, with an OLS
trend line. The simplest of the charges charts — `charges_totales_chf`
needs no MCH1/MCH2 break (unlike every by-nature breakdown above it,
it's already one continuous series across the standard switch, see
`scripts/11_charges_etat.py`), so this is a single unbroken line, no
`plot_broken_series` needed. The full 1993-2024 line is drawn for
context, but the regression is fit only on **2014-2024**, the same
window used in `scripts/26_charges_transfert_trend.py` and
`scripts/32_subsides_maladie_total.py`, so all three trends are
comparable on equal footing. As of the last run:
**+0.1486 percentage points/year** of one median salary (95% CI
[0.0621, 0.2352], R² = 0.63, p = 0.0037) — significant, but a looser
fit than subsides maladie's (R² = 0.84), consistent with "total
charges" bundling flatter categories (e.g. biens et services, per
`24_charges_main_categories.py`) in alongside the fast-growing ones.

`scripts/28_charges_transfert_fonctionnel.py` builds
`charges_transfert_fonctionnel_median_salary_ratio.png` (+ its `.csv`):
the same charges de transfert as scripts 24/26, but broken down by
*functional* classification (what it's spent on: health, education,
social welfare, ...) instead of by nature — same unit as
`26_charges_transfert_trend.py`, so directly comparable, and no
MCH1/MCH2 break needed (functional classification is MCH2-only in this
pipeline). 5 named functions — Prévoyance sociale, Santé, Formation,
Trafic et télécommunications, Finances et impôts — cover ~95% of the
total cumulated over 2014-2024; the rest is bucketed into a 6th
"Autres" residual, same pattern as `24_charges_main_categories.py`.
**Prévoyance sociale** (social welfare) is clearly the main driver of
the growth seen in the aggregate charges-de-transfert charts — it's
both the largest function and the one still visibly climbing through
2024-2025, while **Santé** and **Formation** are smaller and much
flatter. This chart runs through **2025**, one year further than every
other charges chart, because its source
(`Charges_de_transfert_par_classification_fonctionnelle.xlsx`) already
has a 2025 column that the general "5.2" charges-by-nature report
doesn't yet — usable here since `population_canton` and
`salaire_median_vaud_approx_chf` both already reach 2025 too.

`scripts/29_charges_transfert_fonctionnel_top4.py` builds
`charges_transfert_fonctionnel_top4_median_salary_ratio.png` (+ its
`.csv`): a simpler companion to script 28 — just the 4 biggest
functions (Prévoyance sociale, Santé, Formation, Finances et impôts) as
their own lines, **no "Autres" residual**. Unlike script 28's 6-line
chart, this one doesn't sum to the charges-de-transfert total; it's a
focused look at the 4 largest drivers, not a full decomposition. Same
unit, so directly comparable to scripts 26 and 28.

`scripts/30_charges_transfert_prevoyance_detail.py` builds
`charges_transfert_prevoyance_detail_median_salary_ratio.png` (+ its
`.csv`): drills into Prévoyance sociale itself (the main driver
identified by scripts 28-29), split into its 6 functional
sub-categories — Aide sociale et asile, Maladie et accident,
Invalidité, Famille et jeunesse, Vieillesse et survivants, Chômage.
Unlike every other 6-line chart in this pipeline, there's **no
"Autres" residual**: these 6 sub-codes (51/52/53/54/55/57) are a
complete partition of code "5" in the source (56/58/59 don't exist),
summing almost exactly to `charges_transfert_prevoyance_sociale_chf`
(checked in `scripts/12_charges_transfert_fonctionnel.py`, tolerance
1500 CHF for source rounding). The picture: **Maladie et accident**
(subsidized health-insurance premiums) roughly tripled per inhabitant
from 2014 to 2025 and is closing in on **Aide sociale et asile**
(social aid/asylum), which was already the largest sub-category and
has also kept climbing — between them they explain most of Prévoyance
sociale's, and therefore most of charges de transfert's, growth. The
other four sub-categories are smaller and much flatter.

`scripts/31_subsides_maladie_chart.py` builds
`subsides_maladie_median_salary_ratio.png` (+ its `.csv`): a different
source than scripts 28-30 (DGCS / Office vaudois de l'assurance-maladie,
not the MCH2 nature/functional reports) — cantonal LAMal premium
subsidies, 1986-2024, split by the 4 beneficiary types the source
itself defines. These sum exactly to the source's own Total (checked
in `scripts/13_subsides_maladie.py`), so no "Autres" residual, same
pattern as script 30. Two of the 4 are complementary in time rather
than overlapping — "Collectif personnes âgées" was discontinued and
"RI et assimilés / cas de rigueur" introduced the same year (1996,
when LAMal took effect) — so each is drawn via `gap_segments`, not
interpolated across that boundary. **Subsidiés partiels** is both the
largest category and the one that has grown the fastest, especially
since ~2016 — consistent with (though not cross-checked against, since
the two sources may differ in scope) the "Maladie et accident" rise
found in script 30.

`scripts/32_subsides_maladie_total.py` builds
`subsides_maladie_total_median_salary_ratio.png` (+ its `.csv`): just
`subsides_maladie_total_chf`, no category split, with an OLS trend line
— same simplification script 27 applies to total charges. The full
1986-2024 line is drawn for context, but (per request) the regression
is fit only on **2014-2024**, the same recent window used in
`scripts/26_charges_transfert_trend.py`, since that's where the
steepest rise is and the number worth quantifying — not the full
39-year span. As of the last run: **+0.0466 percentage points/year**
of one median salary (95% CI [0.0314, 0.0617], R² = 0.84, p ≈
6.6e-05) — a clear, statistically significant acceleration.

## Layout

```
justfile      the `just` recipes described above
fichiers/     raw source files (untouched)
scripts/      01-19 extraction scripts, 20_build_master.py, 21/22_charts*.py
clean/        tidy per-source CSVs (year, <value...>), regenerated each run
output/       output/vaud_taxes_master.csv, the final merged table
charts/       PNG charts + their underlying derived CSV
```
