"""Primitives — smoke-test every drawing helper on a dummy axis."""
from __future__ import annotations

import matplotlib.pyplot as plt

from figures.core import primitives as P


def _fresh():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    return fig, ax


def test_panel_label_places_text() -> None:
    fig, ax = _fresh()
    P.panel_label(ax, "A")
    assert any(t.get_text() == "A" for t in ax.texts)
    plt.close(fig)


def test_tile_title_caps_to_three_words() -> None:
    fig, ax = _fresh()
    P.tile_title(ax, "one two three four five")
    title = ax.get_title()
    assert len(title.split()) <= 3
    plt.close(fig)


def test_halo_and_callout_and_fmt() -> None:
    fig, ax = _fresh()
    P.halo_text(ax, 0.5, 0.5, "mark")
    P.callout_box(ax, 0.02, 0.98, "note")
    assert P.smart_fmt(0.001) == "0.001"
    assert P.smart_fmt(1.234) == "1.23"
    plt.close(fig)


def test_stable_saddle_dashed_and_significance() -> None:
    fig, ax = _fresh()
    P.stable_fixed_point(ax, 0.5, 0.5, color="#111", name="home")
    P.saddle_marker(ax, 0.7, 0.3)
    P.dashed_reference(ax, 0.5, axis="x", label="cut")
    P.dashed_reference(ax, 0.5, axis="y", label="cut")
    P.significance_bracket(ax, 0.1, 0.9, 0.95, text="**")
    plt.close(fig)


def test_scale_bar_respects_axes_fraction() -> None:
    fig, ax = _fresh()
    P.scale_bar(ax, 5.0, location="lower right")
    plt.close(fig)


def test_suptitle_stack_and_apply_spine_style() -> None:
    fig, ax = _fresh()
    P.apply_spine_style(ax)
    P.suptitle_stack(fig, "hero", subtitle="sub")
    plt.close(fig)


def test_iter_palette_cycles() -> None:
    assert P.iter_palette(["#111", "#222"], 5) == ["#111", "#222", "#111", "#222", "#111"]
