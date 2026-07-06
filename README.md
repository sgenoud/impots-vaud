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
- `just all` — (depends on `charts` and `charts-vevey`) builds
  everything.
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

`scripts/21_charts.py` builds three PNGs plus the numbers behind them,
all in `charts/`:

- `taxes_per_capita_chf.png` — cantonal tax, all-communes tax, and the
  two combined, in CHF per inhabitant (`taxes_*_chf / population_canton`).
- `taxes_per_capita_pct_median_salary.png` — the same three series
  expressed as a percentage of one median annual Vaud salary
  (`salaire_median_vaud_approx_chf x 12`), i.e. how many median annual
  salaries the per-inhabitant tax bill is worth. Since this leans on
  the *approximated* salary series, most of its year-to-year shape
  before 2012 and between anchors is modeled, not measured — see the
  gap note above.
- `taxes_per_capita_pct_pib.png` — tax revenue as a percentage of real
  GDP (`taxes_*_chf / pib_reel_chf`, chained to prior-year prices,
  ref. year 2025). This chart isn't per capita at all — population
  cancels out of `(taxes/pop) / (pib/pop)`, so revenue-over-GDP is the
  same ratio computed directly from the totals. Only 1997-2024, since
  GDP starts in 1997.
- `taxes_per_capita.csv` — the derived per-capita, per-salary, and
  per-PIB figures behind all three charts, for inspection or further
  analysis.

The CHF and salary-share charts are restricted to 1990-2024 (where
both tax series exist); the PIB-share chart to 1997-2024 (where GDP
also exists). Styling follows the project's dataviz skill: a validated
categorical palette (`scripts/_chart_style.py`), thin lines, recessive
gridlines,
and direct end-of-line labels.

`scripts/22_charts_vevey.py` builds the same two charts for Vevey
alone (a single series, since there's no canton/communes split at
commune level): `taxes_vevey_per_capita_chf.png`,
`taxes_vevey_per_capita_pct_median_salary.png`, and
`taxes_vevey_per_capita.csv`. Same 1990-2024 restriction (where
`taxes_vevey_chf` exists) and same salary caveat — plus note this
compares a commune-level tax to a canton-level salary, since no
Vevey-specific salary data exists.

## Layout

```
justfile      the `just` recipes described above
fichiers/     raw source files (untouched)
scripts/      01-19 extraction scripts, 20_build_master.py, 21/22_charts*.py
clean/        tidy per-source CSVs (year, <value...>), regenerated each run
output/       output/vaud_taxes_master.csv, the final merged table
charts/       PNG charts + their underlying derived CSV
```
