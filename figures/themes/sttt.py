"""Signal Transduction and Targeted Therapy theme — looser layout."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 8.5,
    "axes.labelsize": 8.5,
    "axes.titlesize": 9.5,
    "figure.subplot.hspace": 0.5,
    "figure.subplot.wspace": 0.38,
}


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    _ = fig
