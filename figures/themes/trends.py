"""Trends reviews theme — full-page figures with wide margins."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 9.0,
    "axes.labelsize": 9.0,
    "axes.titlesize": 10.5,
    "figure.subplot.hspace": 0.55,
    "figure.subplot.wspace": 0.42,
}


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    _ = fig
