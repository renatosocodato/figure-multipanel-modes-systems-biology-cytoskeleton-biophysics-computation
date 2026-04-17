from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


SANS_STACK = ["Helvetica", "Helvetica Neue", "Arial", "Liberation Sans", "DejaVu Sans", "sans-serif"]

MINIMAL_PARAMS = {
    "font.family": "sans-serif",
    "font.sans-serif": SANS_STACK,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 6.0,
    "axes.labelsize": 9,
    "axes.labelweight": "regular",
    "axes.labelcolor": "#111827",
    "axes.edgecolor": "#4B5563",
    "axes.linewidth": 0.6,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.color": "#4B5563",
    "ytick.color": "#4B5563",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "axes.axisbelow": True,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
}


NOTE_STYLES = {
    "ok":     {"face": "#F0FDF4", "edge": "#16A34A", "text": "#166534"},
    "warn":   {"face": "#FEF2F2", "edge": "#DC2626", "text": "#991B1B"},
    "info":   {"face": "#F9FAFB", "edge": "#9CA3AF", "text": "#1F2937"},
    "accent": {"face": "#F5F3FF", "edge": "#7C3AED", "text": "#5B21B6"},
}

SEPARATOR_COLOR = "#D1D5DB"
PANEL_LABEL_COLOR = "#111827"
MAX_TITLE_WORDS = 3


def short_title(value: Optional[str], max_words: int = MAX_TITLE_WORDS) -> str:
    """Collapse whitespace, strip line breaks, and cap at ``max_words`` tokens."""

    if value is None:
        return ""
    words = str(value).replace("\n", " ").replace("\r", " ").split()
    return " ".join(words[:max_words])


def enforce_minimal_theme(ax=None) -> None:
    """Apply the publication baseline style globally and to a specific axes."""

    plt.rcParams.update(MINIMAL_PARAMS)
    if ax is None:
        ax = plt.gca()
    if ax is None:
        return
    ax.tick_params(labelsize=8, color="#4B5563")
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#4B5563")
        ax.spines[side].set_linewidth(0.6)


def panel_label(ax, letter: str, *, x: float = -0.14, y: float = 1.08, fontsize: int = 14) -> None:
    """Render a large bold panel label (A, B, C…) anchored outside the axes top-left."""

    if ax is None or not letter:
        return
    ax.text(
        x,
        y,
        str(letter).strip(),
        transform=ax.transAxes,
        fontsize=fontsize,
        fontweight="bold",
        color=PANEL_LABEL_COLOR,
        va="bottom",
        ha="left",
    )


def tile_axes(
    ax,
    panel_label_letter: str,
    title: str,
    subtitle: str = "",  # kept for API compatibility; not rendered (no footer / meta line).
    status: Optional[str] = None,  # kept for API compatibility; not rendered.
) -> None:
    """Render the panel label and a centered single-line title of at most three words."""

    if ax is None:
        return
    panel_label(ax, panel_label_letter)
    trimmed = short_title(title)
    if trimmed:
        ax.set_title(
            trimmed,
            loc="center",
            fontsize=10,
            fontweight="bold",
            color=PANEL_LABEL_COLOR,
            pad=8,
            wrap=False,
        )


def annotation_note(
    ax,
    x: float,
    y: float,
    text: str,
    *,
    kind: str = "info",
    fontsize: int = 7.5,
    ha: str = "left",
    va: str = "bottom",
) -> None:
    """Draw an in-axes annotation pill (ok/warn/info/accent)."""

    if ax is None or not text:
        return
    style = NOTE_STYLES.get(kind, NOTE_STYLES["info"])
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        fontsize=fontsize,
        color=style["text"],
        ha=ha,
        va=va,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": style["face"],
            "edgecolor": style["edge"],
            "linewidth": 0.6,
        },
    )


def row_separator(fig, y: float, *, left: float = 0.04, right: float = 0.96, linewidth: float = 0.5) -> None:
    """Draw a thin grey horizontal rule across the figure to separate panel rows."""

    if fig is None:
        return
    fig.add_artist(
        plt.Line2D(
            [left, right],
            [y, y],
            transform=fig.transFigure,
            color=SEPARATOR_COLOR,
            linewidth=linewidth,
            solid_capstyle="butt",
        )
    )
