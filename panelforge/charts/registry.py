from __future__ import annotations

from typing import Any, Callable, Dict

from .base import RenderContext
from . import univariate, bivariate, compositional, multivariate, diagnostics


Renderer = Callable[[RenderContext, str, Any], tuple]


class ChartRegistry:
    """Registry for chart type handlers.

    Handlers are expected to accept ``(ctx, chart_type, panel)`` or (ctx, panel)
    via convenience wrappers inside each group module.
    """

    def __init__(self):
        self._by_name: Dict[str, Renderer] = {}
        self._install_defaults()

    def _install_defaults(self):
        for name in [
            "bar",
            "lollipop",
            "hist",
            "histogram",
            "kde",
            "ecdf",
            "box",
            "violin",
            "dot",
            "dot_plot",
            "split_violin",
            "ridge_distribution",
        ]:
            self._by_name[name] = lambda ctx, _n, panel=None, _f=univariate.render: _f(ctx, _n, panel=panel)

        for name in ["scatter", "line", "area", "stacked_area", "regression", "regression_ci", "hexbin", "correlogram", "phase_portrait", "hierarchical_ci_line"]:
            self._by_name[name] = lambda ctx, _n, panel=None, _f=bivariate.render: _f(ctx, _n, panel=panel)

        for name in ["heatmap", "cluster_heatmap", "corr_matrix", "pca", "pca_scatter", "tsne", "tsne_scatter", "umap", "umap_scatter"]:
            self._by_name[name] = lambda ctx, _n, panel=None, _f=multivariate.render: _f(ctx, _n, panel=panel)

        for name in ["stacked_bar", "stacked_bar_100", "outcome_composition", "tally_tiles", "sobol_bar"]:
            self._by_name[name] = lambda ctx, _n, panel=None, _f=compositional.render: _f(ctx, _n, panel=panel)

        for name in ["roc", "pr", "precision_recall", "calibration", "residuals", "qq", "ma", "volcano", "manhattan"]:
            self._by_name[name] = lambda ctx, _n, panel=None, _f=diagnostics.render: _f(ctx, _n, panel=panel)

    def register(self, chart_type: str, fn: Renderer) -> None:
        self._by_name[chart_type] = fn

    def resolve(self, chart_type: str) -> Renderer:
        if chart_type in self._by_name:
            return self._by_name[chart_type]
        raise KeyError(f"Unsupported chart type: {chart_type}")


registry = ChartRegistry()

