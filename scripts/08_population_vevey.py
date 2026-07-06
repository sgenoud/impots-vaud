"""Vevey population, 1981-2025.

Two sources:

1. fichiers/px-x-0102020000_201.px -- OFS "Bilan démographique selon le
   niveau géographique institutionnel", a PX-file covering every Swiss
   commune, 1981-2024. It's a full cartesian product of
   (Année x Commune x Nationalité x Sexe) rows, each holding 18
   demographic-component values (HEADING axis); we want the
   "Effectif au 31 décembre" (population at Dec 31) component, for
   Vevey, nationality=total, sexe=total. The file is 46MB but its DATA
   block is one line per (year, region, nationality, sex) combination
   in a fixed, computable order, so we stream through it and only keep
   the ~44 lines we need rather than loading it whole.

2. fichiers/2. Population résidante permanente par origine, sexe,
   district et commune, Vaud, 2017-2025.xlsx -- used only for 2025,
   since the .px file stops at 2024. Its 2017-2024 values differ from
   the .px file by a handful of people (different data vintage /
   revision), so the .px series is treated as authoritative where both
   exist and this file only fills the one extra year.

Output: clean/population_vevey.csv (year, population_vevey)
"""
import re
import pandas as pd
from _lib import FICHIERS, CLEAN

PX_PATH = f"{FICHIERS}/px-x-0102020000_201.px"
XLSX_PATH = (
    f"{FICHIERS}/2. Population résidante permanente par origine, sexe, "
    f"district et commune, Vaud, 2017-2025.xlsx"
)

REGION_LABEL = "......5890 Vevey"
COMPONENT_LABEL = "Effectif au 31 décembre"
NAT_LABEL = "Nationalité (catégorie) - total"
SEX_LABEL = "Sexe - total"


def get_values(meta: str, key: str, lang: str | None = None) -> list[str]:
    tag = f"[{lang}]" if lang else ""
    pattern = r'VALUES' + re.escape(tag) + r'\("' + re.escape(key) + r'"\)\s*=\s*(.*?);'
    m = re.search(pattern, meta, re.S)
    if not m:
        raise ValueError(f"VALUES{tag}({key!r}) not found")
    return re.findall(r'"(.*?)"', m.group(1), re.S)


# --- read just the metadata header (well under 1MB) to compute axis indices ---
with open(PX_PATH, encoding="iso-8859-15") as f:
    meta = f.read(400_000)
    assert "\nDATA=" in meta, "metadata block bigger than expected, widen the read"

years = get_values(meta, "Année", "fr")
regions = get_values(meta, "Canton (-) / District (>>) / Commune (......)", "fr")
nats = get_values(meta, "Nationalité (catégorie)", "fr")
sexes = get_values(meta, "Sexe", "fr")
components = get_values(meta, "Composante démographique", "fr")

n_region, n_nat, n_sex, n_comp = len(regions), len(nats), len(sexes), len(components)
region_idx = regions.index(REGION_LABEL)
nat_idx = nats.index(NAT_LABEL)
sex_idx = sexes.index(SEX_LABEL)
comp_idx = components.index(COMPONENT_LABEL)

# each DATA line = one (year, region, nationality, sex) combination,
# holding n_comp component values; nat/sex are fixed to "total" here so
# they only contribute a constant offset per year/region combination.
target_line_of_year = {
    int(year): (year_i * n_region + region_idx) * n_nat * n_sex + nat_idx * n_sex + sex_idx
    for year_i, year in enumerate(years)
}
line_to_year = {v: k for k, v in target_line_of_year.items()}

px_values: dict[int, int] = {}
with open(PX_PATH, encoding="iso-8859-15") as f:
    in_data = False
    line_counter = -1
    for line in f:
        if not in_data:
            if line.strip() == "DATA=":
                in_data = True
            continue
        stripped = line.strip()
        if not stripped or stripped == ";":
            continue
        line_counter += 1
        if line_counter in line_to_year:
            nums = stripped.split()
            px_values[line_to_year[line_counter]] = int(nums[comp_idx])
            if len(px_values) == len(line_to_year):
                break

# --- 2025 only, from the annual per-commune population file ---
xdf = pd.read_excel(XLSX_PATH, sheet_name="Total, Total", header=None)
header_row = 7
vevey_row = xdf[(xdf[1] == "Vevey") & (xdf[2] == 5890)].index[0]
year_2025_col = [
    c for c in xdf.columns if str(xdf.iloc[header_row, c]).strip() == "2025"
][0]
px_values[2025] = int(xdf.iloc[vevey_row, year_2025_col])

out = pd.DataFrame(
    sorted(px_values.items()), columns=["year", "population_vevey"]
)
out.to_csv(f"{CLEAN}/population_vevey.csv", index=False)
print(f"wrote {len(out)} rows -> clean/population_vevey.csv "
      f"({out.year.min()}-{out.year.max()})")
