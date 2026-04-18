"""PNAS theme — 8.7 cm single / 17.8 cm double, Helvetica-first."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 8.0,
    "axes.labelsize": 8.0,
    "axes.titlesize": 9.0,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "legend.fontsize": 7.0,
    "mathtext.fontset": "dejavusans",
}

SINGLE_WIDTH_IN = 3.425  # 87 mm
DOUBLE_WIDTH_IN = 7.008  # 178 mm


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    if fig is not None:
        w, h = fig.get_size_inches()
        target = SINGLE_WIDTH_IN if w <= SINGLE_WIDTH_IN + 0.3 else DOUBLE_WIDTH_IN
        fig.set_size_inches(min(w, target), h)
