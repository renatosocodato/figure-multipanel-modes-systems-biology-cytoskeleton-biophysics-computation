"""Smoke-test every recipe against its ``demo_input`` fixture.

We iterate over :data:`figures.recipes.RECIPE_REGISTRY`, build an axes,
call the recipe, and assert that the axes has drawn something or that
the recipe finished without raising. This catches regressions in recipe
signatures, contract validation, and palette wiring.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from figures.core.style import apply_style
from figures.recipes import RECIPE_REGISTRY


@pytest.mark.parametrize("name", sorted(RECIPE_REGISTRY))
def test_recipe_smoke(name: str) -> None:
    apply_style()
    recipe_fn, demo_fn = RECIPE_REGISTRY[name]
    contract = demo_fn()
    fig, ax = plt.subplots(figsize=(4, 3))
    try:
        returned = recipe_fn(ax, contract)
        assert returned is ax, f"{name}: recipe must return the passed axes"
        # Either the axes has some drawable artist, or (for heavily decorated
        # compositions like heatmaps) the figure has spawned sub-axes.
        has_artist = (
            ax.has_data()
            or any(a is not ax for a in fig.get_axes())
            or ax.texts
            or ax.collections
            or ax.patches
            or ax.images
        )
        assert has_artist, f"{name}: recipe produced no drawable output"
    finally:
        plt.close(fig)


def test_every_recipe_has_demo_entry() -> None:
    for name, (fn, demo) in RECIPE_REGISTRY.items():
        assert callable(fn)
        assert callable(demo)
