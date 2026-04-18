"""Neuron theme — Cell family variant with richer annotation spacing."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 8.0,
    "axes.labelsize": 8.0,
    "axes.titlesize": 9.5,
    "figure.subplot.hspace": 0.45,
    "figure.subplot.wspace": 0.34,
}


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    _ = fig
