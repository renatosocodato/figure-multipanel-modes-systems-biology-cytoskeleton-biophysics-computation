"""Biophysical Journal theme — accepts Type 3 fonts as fallback."""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


OVERRIDES = {
    "font.size": 8.0,
    "axes.labelsize": 8.0,
    "axes.titlesize": 9.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,  # prefer Type 42 but allow Type 3 fallback downstream
    "mathtext.fontset": "stix",
}


def apply(fig: Optional[plt.Figure] = None) -> None:
    plt.rcParams.update(OVERRIDES)
    _ = fig
