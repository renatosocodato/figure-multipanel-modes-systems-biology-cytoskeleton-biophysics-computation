"""Regression tests for P1/P2 fixes on PR #3."""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import pytest

from figures.core.contract import (
    AiryscanGridInput,
    BifurcationInput,
    TrajectoryOverlayInput,
)
from figures.core.style import apply_style
from figures.recipes.dynamics import bifurcation
from figures.recipes.embeddings import trajectory_overlay
from figures.recipes.morphometry import airyscan_panel_grid


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
