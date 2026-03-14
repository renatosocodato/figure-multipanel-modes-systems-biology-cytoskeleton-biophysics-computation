from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt


MINIMAL_PARAMS = {
    "font.family": "Arial",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.which": "major",
    "grid.linestyle": "-",
    "grid.linewidth": 0.25,
    "grid.alpha": 0.35,
    "axes.axisbelow": True,
}


def enforce_minimal_theme(ax=None) -> None:
    """Apply minimal scientific style to current or specified axes."""

    plt.rcParams.update(MINIMAL_PARAMS)
    if ax is None:
        ax = plt.gca()
    if ax is None:
        return
    ax.tick_params(labelsize=8)
    ax.set_facecolor("white")
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)


def tile_axes(ax, panel_label: str, title: str, subtitle: str = "", status: Optional[str] = None) -> None:
    """Paint a compact tile-style strip anchored to the axes top-left."""

    if ax is None:
        return
    text = f"[{panel_label}] {title}"
    if subtitle:
        text += f" — {subtitle}"
    if status:
        text += f" | {status}"
    ax.text(
        0,
        1.015,
        text,
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        color="#111827",
        va="bottom",
        ha="left",
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "#F9FAFB", "edgecolor": "#D1D5DB", "alpha": 0.92},
    )

