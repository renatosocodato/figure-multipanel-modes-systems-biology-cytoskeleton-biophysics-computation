"""Developmental Cell theme — Cell family variant."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 8.0,
    "axes.labelsize": 8.0,
    "axes.titlesize": 9.5,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "legend.fontsize": 7.0,
    "mathtext.fontset": "dejavuserif",
}


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    _ = fig  # venue uses caller-provided sizes; no width clamp.
