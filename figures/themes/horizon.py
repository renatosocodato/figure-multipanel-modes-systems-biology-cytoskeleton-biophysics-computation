"""Horizon Europe theme — A4 landscape with room for logos."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 9.0,
    "axes.labelsize": 9.0,
    "axes.titlesize": 10.0,
    "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0,
    "figure.subplot.hspace": 0.40,
    "figure.subplot.wspace": 0.32,
}

A4_LANDSCAPE_IN = (11.69, 8.27)


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    if fig is not None:
        fig.set_size_inches(*A4_LANDSCAPE_IN)
