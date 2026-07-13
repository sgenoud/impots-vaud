# Run `just` with no arguments to list all recipes.
default:
    @just --list

# Run every extraction script: fichiers/* -> clean/*.csv (scripts 01-19)
extract:
    for f in scripts/[0-1][0-9]_*.py; do echo "== $f =="; uv run python "$f"; done

# Merge clean/*.csv into output/vaud_taxes_master.csv
master: extract
    uv run python scripts/20_build_master.py

# Canton + communes tax-per-capita charts (CHF, % median salary, % PIB)
charts: master
    uv run python scripts/21_charts.py

# Vevey tax-per-capita charts (CHF, % median salary)
charts-vevey: master
    uv run python scripts/22_charts_vevey.py

# Charges de personnel as a % of total charges (MCH1/MCH2 break)
charts-charges: master
    uv run python scripts/23_charges_charts.py

# The 6 main charge categories as a % of total charges (MCH1/MCH2 break)
charts-charges-main: master
    uv run python scripts/24_charges_main_categories.py

# Detail of the 6 biggest line items inside "Autres" (MCH2 only, 2014-2024)
charts-charges-autres: master
    uv run python scripts/25_charges_autres_detail.py

# Charges de transfert per capita with an OLS trend line (MCH2, 2014-2024)
charts-charges-transfert-trend: master
    uv run python scripts/26_charges_transfert_trend.py

# Total charges per capita in median-salary units (no MCH1/MCH2 break needed)
charts-charges-totales: master
    uv run python scripts/27_charges_totales_median_salary.py

# Charges de transfert broken down by functional classification (2014-2025)
charts-charges-transfert-fonctionnel: master
    uv run python scripts/28_charges_transfert_fonctionnel.py

# Charges de transfert, 4 main functional categories only (2014-2025)
charts-charges-transfert-fonctionnel-top4: master
    uv run python scripts/29_charges_transfert_fonctionnel_top4.py

# Prévoyance sociale broken down by sub-function (2014-2025)
charts-charges-transfert-prevoyance: master
    uv run python scripts/30_charges_transfert_prevoyance_detail.py

# Subsides aux primes d'assurance-maladie, par type de bénéficiaire (1986-2024)
charts-subsides-maladie: master
    uv run python scripts/31_subsides_maladie_chart.py

# Total subsides aux primes d'assurance-maladie only, no category split (1986-2024)
charts-subsides-maladie-total: master
    uv run python scripts/32_subsides_maladie_total.py

# Full cantonal tax table, stacked by taxpayer/type group (1990-2024)
charts-taxes-canton-par-type: master
    uv run python scripts/33_taxes_canton_par_type.py

# Natural- vs legal-person cantonal taxes, in median-salary units (1990-2024)
charts-taxes-canton-personnes: master
    uv run python scripts/34_taxes_canton_personnes_median_salary.py

# Natural-person tax categories, in median-salary units (1990-2024)
charts-taxes-canton-personnes-categories: master
    uv run python scripts/35_taxes_canton_personnes_physiques_categories_median_salary.py

# Build everything: extraction -> master table -> all charts
all: charts charts-vevey charts-charges charts-charges-main charts-charges-autres charts-charges-transfert-trend charts-charges-totales charts-charges-transfert-fonctionnel charts-charges-transfert-fonctionnel-top4 charts-charges-transfert-prevoyance charts-subsides-maladie charts-subsides-maladie-total charts-taxes-canton-par-type charts-taxes-canton-personnes charts-taxes-canton-personnes-categories

# Run a single script by name, e.g. `just run 02_taxes_canton.py`
run script:
    uv run python scripts/{{script}}

# Remove every generated file for a from-scratch rebuild
clean:
    rm -f clean/*.csv output/*.csv charts/*.png charts/*.csv
