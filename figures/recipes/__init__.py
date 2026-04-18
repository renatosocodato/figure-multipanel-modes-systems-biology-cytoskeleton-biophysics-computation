"""Recipes layer.

Each submodule exposes a ``DEMOS`` dict mapping recipe name to
``(recipe_fn, demo_input_fn)``. The consolidated :data:`RECIPE_REGISTRY`
below is what the smoke tests iterate over, and what downstream code can
use to programmatically look up recipes by name.
"""
from __future__ import annotations

from typing import Callable, Dict, Tuple

from . import (
    composition,
    distributions,
    dynamics,
    embeddings,
    landscape,
    models,
    morphometry,
    omics,
    regression,
    sensitivity,
    stochastic,
    timecourses,
)


RecipeEntry = Tuple[Callable[..., object], Callable[[], object]]


def _merge() -> Dict[str, RecipeEntry]:
    merged: Dict[str, RecipeEntry] = {}
    for module in (
        sensitivity,
        distributions,
        timecourses,
        regression,
        dynamics,
        stochastic,
        morphometry,
        omics,
        embeddings,
        models,
        composition,
        landscape,
    ):
        for name, pair in module.DEMOS.items():
            if name in merged:
                raise RuntimeError(f"duplicate recipe registered: {name}")
            merged[name] = pair
    return merged


RECIPE_REGISTRY: Dict[str, RecipeEntry] = _merge()


__all__ = [
    "RECIPE_REGISTRY",
    "composition",
    "distributions",
    "dynamics",
    "embeddings",
    "landscape",
    "models",
    "morphometry",
    "omics",
    "regression",
    "sensitivity",
    "stochastic",
    "timecourses",
]
