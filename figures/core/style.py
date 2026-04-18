"""Style layer — matplotlib rcParams for publication-grade figures.

Contract
--------
Exposes a single idempotent entry point :func:`apply_style` that writes
rcParams consistent with the system invariants:

* Helvetica-first sans-serif stack with Type 42 font embedding in PDF/PS
  and untouched SVG text for downstream editability.
* 8.5 pt base, 7.5 pt ticks, 9.5 pt bold tile titles, 12 pt suptitle.
* Top/right spines hidden; left/bottom spines ``#333333`` @ 0.7 pt; ticks
  outward.
* No grid, transparent axes, white figure, 600 dpi savefig.

A theme name (e.g. ``"nature"``, ``"cell"``) routes the call through
:mod:`figures.themes` after the defaults are written, so theme overrides
layer on top of the baseline.

Example
-------
>>> from figures.core.style import apply_style
>>> apply_style()             # baseline
>>> apply_style("nature")     # layered theme on top
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import matplotlib.pyplot as plt


SANS_STACK = [
    "Helvetica",
    "Helvetica Neue",
    "Arial",
    "Liberation Sans",
    "DejaVu Sans",
    "sans-serif",
]


BASE_RCPARAMS: Dict[str, Any] = {
    "font.family": "sans-serif",
    "font.sans-serif": SANS_STACK,
    "font.size": 8.5,
    "mathtext.fontset": "dejavuserif",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "center",
    "axes.titlepad": 6.0,
    "axes.labelsize": 8.5,
    "axes.labelcolor": "#111111",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "axes.axisbelow": True,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "legend.fontsize": 7.5,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "figure.dpi": 120,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
    "savefig.transparent": False,
}


#: Named figure size presets, in inches (width, height).
FIGURE_SIZES: Dict[str, tuple[float, float]] = {
    "single": (3.50, 2.80),
    "single_sq": (3.50, 3.50),
    "1p5": (5.20, 3.60),
    "double": (7.20, 4.20),
    "double_sq": (7.20, 7.20),
    "tall": (3.50, 5.00),
    "a4_portrait": (8.27, 11.69),
    "a4_landscape": (11.69, 8.27),
}


def apply_style(theme: Optional[str] = None) -> None:
    """Apply baseline rcParams, then (optionally) layer a theme on top.

    The function is idempotent — calling it multiple times writes the same
    rcParams and does not leak state between themes. A second call with a
    different theme replaces the first cleanly because each call re-applies
    the baseline before dispatching to the theme.
    """

    plt.rcParams.update(BASE_RCPARAMS)
    if theme is None or str(theme).lower() in {"default", "base", ""}:
        return
    from .. import themes  # local import to avoid circular resolution

    apply = getattr(themes, "apply_theme", None)
    if apply is not None:
        apply(theme)


def figsize(preset: str) -> tuple[float, float]:
    """Resolve a named figure-size preset. Returns (width, height) in inches."""

    key = str(preset).lower()
    if key not in FIGURE_SIZES:
        raise KeyError(f"unknown figure-size preset: {preset!r}; known: {sorted(FIGURE_SIZES)}")
    return FIGURE_SIZES[key]
