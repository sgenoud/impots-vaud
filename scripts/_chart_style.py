"""Shared matplotlib styling for scripts/21_charts.py, following the
project's dataviz skill: validated categorical palette (blue/aqua/yellow,
fixed order), thin 2px lines, recessive horizontal-only gridlines, muted
axis ink, legend + direct end-of-line labels (the aqua/yellow slots fall
under 3:1 contrast on a light surface, so visible direct labels are
required, not optional -- see references/palette.md's "relief rule").
"""
import math
import textwrap
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

# Fixed categorical order (slots 1-6) -- validated via
# scripts/validate_palette.py "#2a78d6,#1baf7a,#eda100,#008300,#4a3aa7,#e34948" --mode light
BLUE = "#2a78d6"
AQUA = "#1baf7a"
YELLOW = "#eda100"
GREEN = "#008300"
VIOLET = "#4a3aa7"
RED = "#e34948"


def new_figure():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    return fig, ax


def style_axes(ax, y_formatter):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.tick_params(axis="both", colors=INK_MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=1, zorder=0)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(y_formatter))


def plot_series(ax, x, series):
    """series: list of (label, color, y-values)."""
    for label, color, y in series:
        ax.plot(x, y, color=color, linewidth=2, solid_capstyle="round", zorder=3)
        # direct end-of-line label (relief rule for low-contrast slots)
        last_x, last_y = x[-1], y[-1]
        ax.annotate(
            label,
            xy=(last_x, last_y),
            xytext=(6, 0),
            textcoords="offset points",
            color=color,
            fontsize=10,
            fontweight="bold",
            va="center",
        )


def gap_segments(x, y):
    """Split (x, y) into runs of consecutive non-NaN points -- for a
    series that comes and goes (e.g. a one-off line item some years),
    so plot_broken_series draws a real gap instead of interpolating
    across missing years."""
    segments = []
    cur_x, cur_y = [], []
    for xi, yi in zip(x, y):
        if yi is None or (isinstance(yi, float) and math.isnan(yi)):
            if cur_x:
                segments.append((cur_x, cur_y))
                cur_x, cur_y = [], []
        else:
            cur_x.append(xi)
            cur_y.append(yi)
    if cur_x:
        segments.append((cur_x, cur_y))
    return segments


def plot_broken_series(ax, series, min_label_gap_frac=0.035):
    """series: list of (label, color, segments), where segments is a list
    of (x, y) pairs, each drawn as its own disconnected line -- for series
    that cover a discontinuity (e.g. an accounting-standard switch) rather
    than one continuous run. Only the very last point of the last segment
    gets a direct end-of-line label.

    When several series end close together, their labels are nudged apart
    vertically (keeping their relative order) so the text doesn't overlap
    -- min_label_gap_frac is that minimum spacing, as a fraction of the
    y-axis range, so it scales with whatever unit the chart is in."""
    ends = []
    for label, color, segments in series:
        for x, y in segments:
            ax.plot(x, y, color=color, linewidth=2, solid_capstyle="round", zorder=3)
        last_x, last_y = segments[-1][0][-1], segments[-1][1][-1]
        ends.append([label, color, last_x, last_y])

    y_lo, y_hi = ax.get_ylim()
    min_gap = (y_hi - y_lo) * min_label_gap_frac
    label_ys = [e[3] for e in ends]
    order = sorted(range(len(ends)), key=lambda i: label_ys[i])
    for prev_i, i in zip(order, order[1:]):
        if label_ys[i] - label_ys[prev_i] < min_gap:
            label_ys[i] = label_ys[prev_i] + min_gap

    for (label, color, last_x, last_y), label_y in zip(ends, label_ys):
        ax.annotate(
            label,
            xy=(last_x, last_y),
            xytext=(6, label_y),
            textcoords=("offset points", "data"),
            color=color,
            fontsize=10,
            fontweight="bold",
            va="center",
        )


def add_titles(fig, ax, title, subtitle, source):
    fig.text(0.06, 0.96, title, fontsize=14, fontweight="bold", color=INK_PRIMARY)

    subtitle_lines = textwrap.wrap(subtitle, width=100)
    for i, line in enumerate(subtitle_lines):
        fig.text(0.06, 0.915 - 0.032 * i, line, fontsize=10.5, color=INK_SECONDARY)

    source_lines = source if isinstance(source, list) else [source]
    wrapped_source = [
        wrapped for line in source_lines for wrapped in textwrap.wrap(line, width=125)
    ]
    top_margin = 0.86 - 0.032 * (len(subtitle_lines) - 1)
    bottom_margin = 0.06 + 0.026 * len(wrapped_source)
    for i, line in enumerate(reversed(wrapped_source)):
        fig.text(0.06, 0.012 + 0.026 * i, line, fontsize=8, color=INK_MUTED)
    fig.subplots_adjust(left=0.08, right=0.78, top=top_margin, bottom=bottom_margin)


def save(fig, path):
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
