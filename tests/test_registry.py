from panelforge.charts.registry import registry


def test_required_chart_types_resolve() -> None:
    required_types = [
        "bar",
        "lollipop",
        "hist",
        "kde",
        "ecdf",
        "box",
        "violin",
        "dot",
        "scatter",
        "line",
        "area",
        "regression_ci",
        "hexbin",
        "heatmap",
        "pca",
        "tsne",
        "umap",
        "stacked_bar",
        "tally_tiles",
        "roc",
        "qq",
        "ma",
        "phase_portrait",
        "split_violin",
        "ridge_distribution",
        "hierarchical_ci_line",
        "sobol_bar",
    ]
    for chart_type in required_types:
        assert registry.resolve(chart_type) is not None
