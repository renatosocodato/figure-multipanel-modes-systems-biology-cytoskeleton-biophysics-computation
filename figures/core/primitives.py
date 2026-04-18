"""Stateless drawing primitives shared across recipes.

Contract
--------
Every function in this module takes an existing ``matplotlib.axes.Axes``
(or ``Figure``) and draws onto it. None of them create figures, change
global state, or rely on rcParams beyond what :mod:`figures.core.style`
already guarantees.

Example
-------
>>> import matplotlib.pyplot as plt
>>> from figures.core.primitives import panel_label, smart_fmt
>>> fig, ax = plt.subplots()
>>> panel_label(ax, "A")
>>> smart_fmt(0.00327)
'0.003'
"""
from __future__ import annotations

from typing import Iterable, Optional

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt


PANEL_LABEL_XY = (-0.17, 1.06)
LABEL_COLOR = "#111111"
META_COLOR = "#6B7280"


def panel_label(ax, letter: str, *, xy: tuple[float, float] = PANEL_LABEL_XY,
                fontsize: float = 12.0) -> None:
    """Render a large bold panel label outside the axes top-left."""

    if ax is None or not letter:
        return
    ax.text(
        xy[0], xy[1], str(letter).strip(),
        transform=ax.transAxes, fontsize=fontsize, fontweight="bold",
        color=LABEL_COLOR, va="bottom", ha="left",
    )


def tile_title(ax, text: str, *, max_words: int = 3) -> None:
    """Render a centered, bold, at-most-``max_words`` title above the axes."""

    if ax is None or not text:
        return
    words = str(text).replace("\n", " ").split()
    if len(words) > max_words:
        words = words[:max_words - 1] + [words[max_words - 1].rstrip(",.:;") + "…"]
    ax.set_title(" ".join(words), loc="center", fontsize=9.5,
                 fontweight="bold", color=LABEL_COLOR, pad=6)


def halo_text(ax, x: float, y: float, text: str, *, color: str = LABEL_COLOR,
              fontsize: float = 8.0, fontweight: str = "bold",
              ha: str = "center", va: str = "center") -> None:
    """Draw text with a 2.8 pt white halo so it survives colored backdrops."""

    if ax is None or not text:
        return
    ax.text(
        x, y, text, color=color, fontsize=fontsize, fontweight=fontweight,
        ha=ha, va=va,
        path_effects=[pe.withStroke(linewidth=2.8, foreground="white")],
    )


def callout_box(ax, x: float, y: float, text: str, *, color: str = "#333333",
                fontsize: float = 7.5, ha: str = "left", va: str = "bottom") -> None:
    """White rounded callout with a thin colored border, matching the referent."""

    if ax is None or not text:
        return
    ax.text(
        x, y, text, transform=ax.transAxes, fontsize=fontsize,
        ha=ha, va=va, color=color,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white",
              "edgecolor": color, "linewidth": 0.6},
    )


def right_of_ci_label(ax, upper: float, y: float, text: str, *, color: str = "#333333",
                      pad: float = 0.01, fontsize: float = 7.0) -> None:
    """Place a label to the right of the upper CI end regardless of sign."""

    if ax is None:
        return
    ax.text(upper + pad, y, text, color=color, fontsize=fontsize,
            ha="left", va="center")


def smart_fmt(value: float) -> str:
    """3 decimals when |v| < 0.01, otherwise 2 decimals."""

    if value is None:
        return ""
    v = float(value)
    return f"{v:.3f}" if abs(v) < 0.01 else f"{v:.2f}"


def stable_fixed_point(ax, x: float, y: float, *, color: str = "#111111",
                       name: Optional[str] = None, marker_size: float = 9.0) -> None:
    """Stable fixed point: filled circle with black rim + optional halo'd label."""

    if ax is None:
        return
    ax.plot(x, y, "o", mfc=color, mec="black", mew=0.9, ms=marker_size, zorder=6)
    if name:
        halo_text(ax, x, y, name.upper(), color=color, fontsize=8.5,
                  ha="left", va="bottom")


def saddle_marker(ax, x: float, y: float, *, color: str = "#111111",
                  size: float = 8.0) -> None:
    """Unstable fixed point / saddle: black cross with white halo."""

    if ax is None:
        return
    ax.plot(x, y, "x", color=color, ms=size, mew=1.7, zorder=6,
            path_effects=[pe.withStroke(linewidth=2.8, foreground="white")])


def dashed_reference(ax, value: float, axis: str = "x", *,
                     color: str = "#9E9E9E", label: Optional[str] = None) -> None:
    """Thin dashed reference line at a constant x or y value."""

    if ax is None or axis not in {"x", "y"}:
        return
    if axis == "x":
        ax.axvline(value, color=color, linewidth=0.6, linestyle="--", zorder=1)
        if label:
            ax.text(value, ax.get_ylim()[1], f" {label}", color=color,
                    fontsize=7, va="top", ha="left")
    else:
        ax.axhline(value, color=color, linewidth=0.6, linestyle="--", zorder=1)
        if label:
            ax.text(ax.get_xlim()[1], value, f" {label}", color=color,
                    fontsize=7, va="center", ha="left")


def scale_bar(ax, length_um: float, *, color: str = "#111111",
              location: str = "lower right", linewidth: float = 2.5) -> None:
    """Draw a horizontal scale bar in axes-fraction units with a μm label."""

    if ax is None or length_um <= 0:
        return
    pad = 0.04
    y = pad if "lower" in location else 1.0 - pad
    x_right = 1.0 - pad if "right" in location else pad + length_um / 10.0
    x_left = x_right - 0.12
    ax.plot([x_left, x_right], [y, y], transform=ax.transAxes,
            color=color, linewidth=linewidth, solid_capstyle="butt", zorder=10)
    ax.text((x_left + x_right) / 2.0, y + 0.015, f"{length_um:g} µm",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=7, color=color)


def significance_bracket(ax, x1: float, x2: float, y: float, text: str, *,
                         color: str = "#333333", tick_height: float = 0.02) -> None:
    """Horizontal bracket spanning ``x1..x2`` with a significance label."""

    if ax is None:
        return
    height = max(tick_height, 0.005)
    ax.plot([x1, x1, x2, x2], [y, y + height, y + height, y], color=color,
            linewidth=0.7)
    ax.text((x1 + x2) / 2.0, y + height, text, ha="center", va="bottom",
            fontsize=7, color=color)


def suptitle_stack(fig, title: str, subtitle: str = "") -> None:
    """Two-line figure title: 12 pt bold at y=0.985, 9 pt grey at y=0.955."""

    if fig is None:
        return
    if title:
        fig.text(0.5, 0.985, title, ha="center", va="top",
                 fontsize=12, fontweight="bold", color=LABEL_COLOR)
    if subtitle:
        fig.text(0.5, 0.955, subtitle, ha="center", va="top",
                 fontsize=9, color=META_COLOR)


def apply_spine_style(ax) -> None:
    """Idempotent spine cleanup: top/right hidden, left/bottom graphite@0.7pt."""

    if ax is None:
        return
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#333333")
        ax.spines[side].set_linewidth(0.7)


def close_figure(fig) -> None:
    """Close a figure without leaking it into pyplot's open-figure registry."""

    if fig is None:
        return
    plt.close(fig)


def iter_palette(palette_colors: Iterable[str], n: int) -> list[str]:
    """Return ``n`` colors, cycling through ``palette_colors`` without repeats < len."""

    colors = list(palette_colors) or ["#4C78A8"]
    if n <= len(colors):
        return colors[:n]
    out = []
    i = 0
    while len(out) < n:
        out.append(colors[i % len(colors)])
        i += 1
    return out
