"""Nature family theme — single column 89 mm, sans-serif only."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 7.0,
    "axes.labelsize": 7.0,
    "axes.titlesize": 8.5,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "mathtext.fontset": "dejavusans",
    "axes.titleweight": "bold",
    "figure.subplot.wspace": 0.28,
    "figure.subplot.hspace": 0.38,
}

COLUMN_WIDTH_IN = 3.503  # 89 mm


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    if fig is not None:
        w, h = fig.get_size_inches()
        fig.set_size_inches(min(w, COLUMN_WIDTH_IN), h)
