"""Core layer — style, palettes, primitives, layout, export, contracts."""
from __future__ import annotations

from .contract import FigureContract
from .export import export_figure
from .layout import figure_with_grid, resolve_shape
from .palette import Palette, get_palette, list_palettes, register_palette, semantic
from .primitives import (
    apply_spine_style,
    callout_box,
    close_figure,
    dashed_reference,
    halo_text,
    panel_label,
    right_of_ci_label,
    saddle_marker,
    scale_bar,
    significance_bracket,
    smart_fmt,
    stable_fixed_point,
    suptitle_stack,
    tile_title,
)
from .style import BASE_RCPARAMS, FIGURE_SIZES, apply_style, figsize

__all__ = [
    "BASE_RCPARAMS",
    "FIGURE_SIZES",
    "FigureContract",
    "Palette",
    "apply_spine_style",
    "apply_style",
    "callout_box",
    "close_figure",
    "dashed_reference",
    "export_figure",
    "figsize",
    "figure_with_grid",
    "get_palette",
    "halo_text",
    "list_palettes",
    "panel_label",
    "register_palette",
    "resolve_shape",
    "right_of_ci_label",
    "saddle_marker",
    "scale_bar",
    "semantic",
    "significance_bracket",
    "smart_fmt",
    "stable_fixed_point",
    "suptitle_stack",
    "tile_title",
]
