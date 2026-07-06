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

# Build everything: extraction -> master table -> all charts
all: charts charts-vevey

# Run a single script by name, e.g. `just run 02_taxes_canton.py`
run script:
    uv run python scripts/{{script}}

# Remove every generated file for a from-scratch rebuild
clean:
    rm -f clean/*.csv output/*.csv charts/*.png charts/*.csv
