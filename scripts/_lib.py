"""Shared helpers for the extraction scripts.

Every extraction script reads one raw file from fichiers/ and writes one
tidy CSV (columns: year, <value...>) to clean/. Keeping this logic small
and shared makes each extraction script easy to read end-to-end.
"""
import re
import pandas as pd

FICHIERS = "fichiers"
CLEAN = "clean"


def year_from_label(label) -> int | None:
    """Pull a 4-digit year out of a cell that may be '2015', 2015.0,
    '2022p', '2026*', '2017 (2)', etc. Returns None if no year found."""
    m = re.search(r"(19|20)\d{2}", str(label))
    return int(m.group(0)) if m else None


def row_by_label(df: pd.DataFrame, label: str, col: int = 0) -> int:
    """Find the row index whose given column exactly matches `label`
    (after stripping whitespace). Raises if not found, so a structure
    change in the source file fails loudly instead of silently."""
    stripped = df.iloc[:, col].astype(str).str.strip()
    matches = stripped[stripped == label].index
    if len(matches) == 0:
        raise ValueError(f"label {label!r} not found in column {col}")
    return matches[0]
