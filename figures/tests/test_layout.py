"""Layout — figure_with_grid honors the mandated composition grid."""
from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from figures.core.layout import figure_with_grid, resolve_shape


MANDATED = [
    (4, (2, 2)),
    (5, (3, 2)),
    (6, (3, 3)),
    (7, (4, 3)),
    (9, (3, 3)),
]


@pytest.mark.parametrize("count,expected", MANDATED)
def test_resolve_shape_matches_mandated_grid(count, expected) -> None:
    assert resolve_shape(count) == expected


def test_figure_with_grid_returns_requested_panel_count() -> None:
    fig, axes = figure_with_grid(4, figsize="double_sq")
    assert len(axes) == 4
    assert all(t.get_text() != "" for t in axes[0].texts)  # panel label "A"
    plt.close(fig)


def test_figure_with_grid_accepts_tuple_shape() -> None:
    fig, axes = figure_with_grid(3, shape=(1, 3), figsize="double")
    assert len(axes) == 3
    plt.close(fig)


def test_figure_with_grid_five_panels_uses_3x2_gridspec() -> None:
    fig, axes = figure_with_grid(5, figsize="double_sq")
    assert len(axes) == 5
    # The gridspec allocated six cells (3 rows × 2 cols), but the sixth was
    # removed via delaxes so the layout engine ignores it cleanly.
    gs = axes[0].get_subplotspec().get_gridspec()
    assert gs.get_geometry() == (3, 2)
    plt.close(fig)
