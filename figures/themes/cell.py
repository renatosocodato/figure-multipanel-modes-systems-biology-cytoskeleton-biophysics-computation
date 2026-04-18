"""Cell family theme — double column, allows serif in math, 600 dpi."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 8.0,
    "axes.labelsize": 8.0,
    "axes.titlesize": 9.5,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "mathtext.fontset": "dejavuserif",
    "savefig.dpi": 600,
}

DOUBLE_WIDTH_IN = 7.09  # 180 mm


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    if fig is not None:
        w, h = fig.get_size_inches()
        fig.set_size_inches(min(w, DOUBLE_WIDTH_IN), h)
