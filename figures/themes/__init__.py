"""Venue-specific themes layered on top of the baseline style.

Each theme module exports ``apply(fig=None)`` that rewrites selected rcParams
and, when given a Figure, adjusts its size to the venue's column spec.
The canonical entry point is :func:`apply_theme`, which dispatches by name.
"""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt

from . import (
    bpj,
    cell,
    devcell,
    fct_grant,
    horizon,
    ncb,
    nature,
    neuron,
    pnas,
    sttt,
    trends,
)


_THEMES = {
    "nature": nature,
    "cell": cell,
    "pnas": pnas,
    "devcell": devcell,
    "bpj": bpj,
    "neuron": neuron,
    "ncb": ncb,
    "sttt": sttt,
    "trends": trends,
    "fct_grant": fct_grant,
    "horizon": horizon,
}


def apply_theme(name: str, fig: Optional[plt.Figure] = None) -> None:
    """Dispatch to the named theme's ``apply`` callable."""

    key = str(name).lower()
    if key not in _THEMES:
        raise KeyError(f"unknown theme {name!r}; known: {sorted(_THEMES)}")
    _THEMES[key].apply(fig)


__all__ = ["apply_theme"] + list(_THEMES)
