"""Theme switching — applying a second theme overrides the first cleanly."""
from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from figures.core.style import apply_style
from figures.themes import apply_theme


def test_unknown_theme_raises() -> None:
    with pytest.raises(KeyError):
        apply_theme("not_a_theme")


def test_apply_style_then_switch() -> None:
    apply_style("nature")
    nature_size = plt.rcParams["font.size"]
    apply_style("pnas")
    pnas_size = plt.rcParams["font.size"]
    assert pnas_size == 8.0
    assert nature_size == 7.0
    # Switching back should take, confirming no leftover state.
    apply_style("nature")
    assert plt.rcParams["font.size"] == 7.0


def test_apply_theme_resizes_figure_for_nature() -> None:
    from figures.themes.nature import COLUMN_WIDTH_IN

    apply_style()
    fig = plt.figure(figsize=(6.0, 4.0))
    apply_theme("nature", fig)
    w, h = fig.get_size_inches()
    assert pytest.approx(w, rel=1e-3) == COLUMN_WIDTH_IN
    assert h == 4.0
    plt.close(fig)
