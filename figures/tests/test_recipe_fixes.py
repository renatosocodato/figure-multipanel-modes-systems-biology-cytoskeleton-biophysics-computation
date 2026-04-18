"""Regression tests for P1/P2 fixes on PR #3."""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import pytest

from figures.core.contract import (
    AiryscanGridInput,
    BifurcationInput,
    DoseResponseInput,
    TrajectoryOverlayInput,
)
from figures.core.layout import figure_with_grid
from figures.core.style import apply_style
from figures.recipes.dynamics import bifurcation
from figures.recipes.embeddings import trajectory_overlay
from figures.recipes.morphometry import airyscan_panel_grid
from figures.recipes.timecourses import dose_response
from figures.themes.nature import COLUMN_WIDTH_IN


def test_airyscan_panel_grid_handles_empty_image_stack() -> None:
    """Zero thumbnails must not crash with a division-by-zero (P1 review fix)."""

    apply_style()
    empty = np.empty((0, 16, 16), dtype=float)
    fig, ax = plt.subplots(figsize=(3, 2))
    try:
        returned = airyscan_panel_grid(ax, AiryscanGridInput(images=empty))
        assert returned is ax
        # Fallback placeholder rendered instead of thumbnails.
        assert any("no thumbnails" in t.get_text() for t in ax.texts)
    finally:
        plt.close(fig)


def test_bifurcation_saddle_node_marker_is_order_independent() -> None:
    """Marker y must come from the named branch, not whichever dict came first (P2)."""

    apply_style()
    r = np.linspace(0.0, 1.0, 11)
    home = r * 0.2 + 0.15            # 0.15 .. 0.35
    gate = np.full_like(r, 2.5)      # flat
    # Two dicts carrying identical data but different insertion order.
    branches_a = {"home": home, "gate": gate}
    branches_b = {"gate": gate, "home": home}

    def _y_for(branches: dict) -> float:
        fig, ax = plt.subplots(figsize=(3, 2))
        try:
            bifurcation(
                ax,
                BifurcationInput(r=r, branches=branches, saddle_node=0.5,
                                 saddle_node_branch="home"),
            )
            stars = [p for p in ax.collections
                     if p.get_paths() and p.get_sizes().size and p.get_sizes()[0] >= 79]
            assert stars, "saddle-node star missing"
            xy = stars[-1].get_offsets()
            return float(xy[0, 1])
        finally:
            plt.close(fig)

    assert _y_for(branches_a) == pytest.approx(_y_for(branches_b))
    # And it should match the value of the home branch at r=0.5 (=0.25).
    assert _y_for(branches_a) == pytest.approx(0.25, rel=1e-3)


def test_bifurcation_without_branch_key_skips_marker() -> None:
    """A saddle_node without saddle_node_branch must not invent a marker silently."""

    apply_style()
    r = np.linspace(0.0, 1.0, 5)
    fig, ax = plt.subplots(figsize=(3, 2))
    try:
        bifurcation(
            ax,
            BifurcationInput(r=r, branches={"home": r * 0.2}, saddle_node=0.5),
        )
        stars = [p for p in ax.collections
                 if p.get_paths() and p.get_sizes().size and p.get_sizes()[0] >= 79]
        assert not stars, "marker must be skipped when branch is unspecified"
    finally:
        plt.close(fig)


def test_trajectory_overlay_does_not_wrap_last_to_first() -> None:
    """Terminal pseudotime point must not produce an arrow back to the start (P2)."""

    apply_style()
    n = 20
    t = np.linspace(0, 1, n)
    emb = np.column_stack([t * 10.0, np.zeros_like(t)])
    fig, ax = plt.subplots(figsize=(3, 2))
    try:
        trajectory_overlay(ax, TrajectoryOverlayInput(embedding=emb, pseudotime=t))
        quivers = [c for c in ax.collections
                   if c.__class__.__name__ == "Quiver"]
        assert quivers, "expected a quiver overlay"
        n_arrows = len(quivers[-1].get_offsets())
        # Adjacent-pairs recipe emits exactly n-1 arrows. A wrapping recipe would
        # emit n (including the spurious last-to-first arrow).
        assert n_arrows == n - 1, (
            f"expected {n - 1} arrows (src→dst pairs), got {n_arrows} — likely wrapping"
        )
    finally:
        plt.close(fig)


def test_figure_with_grid_applies_theme_fig_sizing() -> None:
    """figure_with_grid must dispatch the theme to fig so width clamps run (P2)."""

    fig, _axes = figure_with_grid(4, figsize="double", theme="nature")
    try:
        w, _ = fig.get_size_inches()
        assert pytest.approx(w, rel=1e-3) == COLUMN_WIDTH_IN, (
            f"theme nature should clamp width to {COLUMN_WIDTH_IN}, got {w}"
        )
    finally:
        plt.close(fig)


def test_dose_response_handles_zero_dose_control() -> None:
    """Zero-dose controls must render (not drop from log axis) and not crash the fit (P2)."""

    apply_style()
    # Include a 0-dose control followed by a log-spaced dose series.
    dose = np.concatenate(([0.0], np.logspace(-2, 2, 8)))
    response = np.concatenate(([0.05], np.linspace(0.1, 1.0, 8)))
    fig, ax = plt.subplots(figsize=(3, 2))
    try:
        dose_response(ax, DoseResponseInput(dose=dose, response=response,
                                            ec50_guess=1.0))
        assert ax.get_xscale() == "symlog", (
            f"zero-dose control should trigger symlog, got {ax.get_xscale()}"
        )
        # The error-bar container holds all plotted points, including the zero-dose one.
        containers = ax.containers
        assert containers, "expected at least one error-bar container"
        xs = containers[0][0].get_xdata()
        assert len(xs) == len(dose), (
            f"expected all {len(dose)} doses to be plotted; got {len(xs)}"
        )
        assert 0.0 in set(np.asarray(xs, dtype=float)), (
            "zero-dose control was dropped from the plot"
        )
    finally:
        plt.close(fig)


def test_figure_with_grid_rejects_undersized_explicit_shape() -> None:
    """Explicit shape with too few cells must raise, not silently drop panels (P2)."""

    with pytest.raises(ValueError, match=r"cells but n_panels=4"):
        figure_with_grid(4, shape=(1, 3), figsize="double")


def test_umap_scatter_highlight_ids_match_metadata_index() -> None:
    """highlight_ids must resolve against metadata.index when no 'id' column exists (P2)."""

    import pandas as pd

    from figures.core.contract import UMAPInput
    from figures.recipes.embeddings import umap_scatter

    apply_style()
    n = 20
    ids = [f"cell_{i:03d}" for i in range(n)]
    emb = np.column_stack([np.linspace(0, 1, n), np.linspace(0, 1, n)])
    meta = pd.DataFrame({"cluster": ["A"] * n}, index=ids)
    targets = ["cell_003", "cell_010", "cell_015"]
    contract = UMAPInput(embedding=emb, metadata=meta, color_col="cluster",
                        continuous=False, density_contours=False,
                        highlight_ids=targets)
    fig, ax = plt.subplots(figsize=(3, 2))
    try:
        umap_scatter(ax, contract)
        # The unfilled highlight scatter renders as a collection with s=25.
        highlight_layers = [
            c for c in ax.collections
            if c.get_sizes().size and np.isclose(c.get_sizes()[0], 25.0)
        ]
        assert highlight_layers, "highlight scatter missing"
        n_marked = len(highlight_layers[-1].get_offsets())
        assert n_marked == len(targets), (
            f"expected {len(targets)} highlighted points, got {n_marked}"
        )
    finally:
        plt.close(fig)


def test_sobol_bar_st_without_st_ci_omits_whiskers() -> None:
    """which='ST' without ST_ci must not fall back to S1_ci (P2)."""

    import pandas as pd  # noqa: F401 — keeps module style consistent with other tests.

    from figures.core.contract import SobolInput
    from figures.recipes.sensitivity import sobol_bar

    apply_style()
    contract = SobolInput(
        parameters=["a", "b", "c"],
        S1=np.array([0.6, 0.3, 0.1]),
        S1_ci=np.array([0.10, 0.02, 0.005]),  # big enough to notice if misapplied
        ST=np.array([0.8, 0.4, 0.2]),
        # ST_ci intentionally omitted.
    )
    fig, ax = plt.subplots(figsize=(3, 2))
    try:
        sobol_bar(ax, contract, which="ST")
        # Error-bar whiskers render as a LineCollection attached to the bar container.
        whisker_lines = [
            c for c in ax.collections
            if c.__class__.__name__ == "LineCollection"
        ]
        assert not whisker_lines, (
            "ST without ST_ci should render without whiskers, not reuse S1_ci"
        )
    finally:
        plt.close(fig)


def test_sobol_bar_st_without_st_values_raises() -> None:
    """which='ST' requires ST values — missing ST must raise, not silently plot S1."""

    from figures.core.contract import SobolInput
    from figures.recipes.sensitivity import sobol_bar

    apply_style()
    contract = SobolInput(parameters=["a"], S1=np.array([0.5]),
                          S1_ci=np.array([0.05]))
    fig, ax = plt.subplots(figsize=(3, 2))
    try:
        with pytest.raises(ValueError, match=r"requires SobolInput\.ST"):
            sobol_bar(ax, contract, which="ST")
    finally:
        plt.close(fig)


def test_calcium_raster_handles_empty_events() -> None:
    """Empty events table must render a placeholder, not crash on NaN bins (P2)."""

    import pandas as pd

    from figures.core.contract import CalciumRasterInput
    from figures.recipes.timecourses import calcium_raster

    apply_style()
    empty = pd.DataFrame({"cell_id": pd.Series([], dtype="int64"),
                          "t": pd.Series([], dtype="float64")})
    fig, ax = plt.subplots(figsize=(3, 2))
    try:
        calcium_raster(ax, CalciumRasterInput(events=empty))
        assert any("no events" in t.get_text() for t in ax.texts)
        # No twin-x axis should have been spawned in the empty case.
        assert len(fig.get_axes()) == 1
    finally:
        plt.close(fig)
