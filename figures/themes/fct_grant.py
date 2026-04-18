"""FCT grant theme — A4 portrait, Portuguese-diacritics-safe, denser layout."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 9.0,
    "axes.labelsize": 9.0,
    "axes.titlesize": 10.0,
    "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0,
    "figure.subplot.hspace": 0.42,
    "figure.subplot.wspace": 0.30,
}

A4_PORTRAIT_IN = (8.27, 11.69)


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    if fig is not None:
        fig.set_size_inches(*A4_PORTRAIT_IN)
