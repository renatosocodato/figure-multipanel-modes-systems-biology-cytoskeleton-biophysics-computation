"""Layout — grid, panel labels, and suptitle assembly.

Contract
--------
:func:`figure_with_grid` constructs ``(fig, axes_list)`` with a gridspec
matching ``n_panels`` (``shape="auto"`` uses the mandated composition
table below), applies the baseline style, places panel letters
``A…Z`` outside each axes, and writes the suptitle/subtitle stack.

Composition table
-----------------
Mirrors the Panelforge rule — applied when ``shape="auto"``:

===== =====
count shape
===== =====
  1   (1,1)
  2   (2,1)
  3   (3,1)
  4   (2,2)
  5   (3,2)
  6   (3,3)
  7   (4,3)
  8   (4,3)
  9   (3,3)
===== =====

Larger counts fall back to the square-ish ceiling layout
``cols = min(4, n)``, ``rows = ceil(n/cols)``.

Example
-------
>>> from figures.core.layout import figure_with_grid
>>> fig, axes = figure_with_grid(4, figsize="double_sq", suptitle="Demo")
>>> len(axes)
4
"""
from __future__ import annotations

import math
from typing import Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt

from .primitives import apply_spine_style, panel_label, suptitle_stack
from .style import apply_style, figsize as _resolve_figsize


MANDATED_GRID: dict[int, Tuple[int, int]] = {
    1: (1, 1),
    2: (2, 1),
    3: (3, 1),
    4: (2, 2),
    5: (3, 2),
    6: (3, 3),
    7: (4, 3),
    8: (4, 3),
    9: (3, 3),
}


def resolve_shape(n: int, shape: str | Tuple[int, int] = "auto") -> Tuple[int, int]:
    """Return ``(rows, cols)`` for a panel count.

    ``shape="auto"`` uses :data:`MANDATED_GRID`; explicit tuples are
    returned unchanged.
    """

    if isinstance(shape, tuple):
        return int(shape[0]), int(shape[1])
    if shape != "auto":
        raise ValueError("shape must be 'auto' or an (rows, cols) tuple")
    if n in MANDATED_GRID:
        return MANDATED_GRID[n]
    cols = min(4, max(1, n))
    rows = math.ceil(n / cols)
    return rows, cols


def _figsize_for(figsize: str | Tuple[float, float]) -> Tuple[float, float]:
    if isinstance(figsize, tuple):
        return float(figsize[0]), float(figsize[1])
    return _resolve_figsize(figsize)


def figure_with_grid(
    n_panels: int,
    *,
    shape: str | Tuple[int, int] = "auto",
    figsize: str | Tuple[float, float] = "double",
    suptitle: str = "",
    subtitle: str = "",
    theme: Optional[str] = None,
    hspace: float = 0.42,
    wspace: float = 0.32,
    labels: Optional[Iterable[str]] = None,
) -> Tuple[plt.Figure, List[plt.Axes]]:
    """Build a grid of axes with panel labels and an optional suptitle stack.

    Parameters
    ----------
    n_panels
        Number of panels to allocate; extra cells (when the grid holds more
        than ``n_panels``) are hidden.
    shape
        ``"auto"`` (default) picks from :data:`MANDATED_GRID`, or an explicit
        ``(rows, cols)`` tuple.
    figsize
        Name from :data:`figures.core.style.FIGURE_SIZES` or an explicit
        ``(width, height)`` tuple.
    suptitle / subtitle
        Optional title stack. Subtitle renders in 9 pt grey under the title.
    theme
        Forwarded to :func:`figures.core.style.apply_style`.
    labels
        Override the default ``A, B, C, ...`` letters.
    """

    apply_style(theme)
    rows, cols = resolve_shape(n_panels, shape)
    if rows * cols < n_panels:
        raise ValueError(
            f"shape={shape!r} yields {rows * cols} cells but n_panels={n_panels}; "
            "panels would be silently dropped. Use 'auto' or widen the grid."
        )
    w, h = _figsize_for(figsize)
    # constrained_layout handles hidden axes correctly; tight_layout warns on them.
    fig, axes_grid = plt.subplots(
        rows, cols, figsize=(w, h), squeeze=False,
        gridspec_kw={"hspace": hspace, "wspace": wspace},
        layout="constrained",
    )
    # Themes that clamp figure width to a journal column (Nature/PNAS/NCB)
    # can only act once the figure exists. Re-dispatch with the fig so the
    # venue-specific sizing actually runs.
    if theme is not None and str(theme).lower() not in {"default", "base", ""}:
        from ..themes import apply_theme as _apply_theme

        _apply_theme(theme, fig)
    flat = axes_grid.reshape(-1).tolist()
    panels = flat[:n_panels]
    # Remove unused cells entirely so the layout engine ignores them.
    for extra in flat[n_panels:]:
        fig.delaxes(extra)

    letters = list(labels) if labels is not None else [chr(ord("A") + i) for i in range(n_panels)]
    for i, ax in enumerate(panels):
        apply_spine_style(ax)
        if i < len(letters):
            panel_label(ax, letters[i])

    if suptitle or subtitle:
        suptitle_stack(fig, suptitle, subtitle)

    return fig, panels
