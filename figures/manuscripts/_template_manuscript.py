"""Template caller — copy this file to start a new manuscript figure script.

Pattern
-------
1. Load or compute data.
2. Build :class:`figures.core.contract.FigureContract` instances for each panel.
3. ``fig, axes = figure_with_grid(n_panels, figsize=..., suptitle=...)``
4. Dispatch each ``ax`` to a recipe.
5. ``export_figure(fig, stem="fig_name", theme=..., palette=...)``

Run this file directly with ``python -m figures.manuscripts._template_manuscript``.
"""
from __future__ import annotations

from figures.core import close_figure, export_figure, figure_with_grid
from figures.recipes import RECIPE_REGISTRY


def build_figure():
    fig, axes = figure_with_grid(
        n_panels=4, figsize="double_sq",
        suptitle="Template figure", subtitle="starter caller",
    )
    # Demo each panel from the recipe registry — replace with real contracts.
    recipes = ["sobol_bar", "split_violin", "phase_portrait", "volcano"]
    for ax, recipe_name in zip(axes, recipes):
        recipe_fn, demo_fn = RECIPE_REGISTRY[recipe_name]
        recipe_fn(ax, demo_fn())
    return fig


def main() -> None:
    fig = build_figure()
    try:
        export_figure(
            fig, stem="template",
            theme="default", palette="okabe_ito",
            script_path=__file__,
        )
    finally:
        close_figure(fig)


if __name__ == "__main__":
    main()
