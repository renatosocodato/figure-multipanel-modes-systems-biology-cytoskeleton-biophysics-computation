"""Morphometry recipes for Airyscan/CZI-derived measurements.

Contains:
    shape_distribution         — pooled violin + per-animal strip
    airyscan_panel_grid        — multi-cell thumbnail grid on a parent GridSpec
    ridge_over_conditions      — ridge convenience wrapper for morphometry
"""
from __future__ import annotations

import numpy as np
from matplotlib.gridspec import GridSpecFromSubplotSpec

from ..core.contract import (
    AiryscanGridInput,
    RidgeInput,
    ShapeDistributionInput,
)
from ..core.palette import get_palette
from ..core.primitives import iter_palette, scale_bar
from .distributions import ridge_by_group


def shape_distribution(ax, contract, palette: str = "cytoskeleton_components"):
    """Pooled violin + per-cluster strip for a single morphometry metric."""

    c = ShapeDistributionInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 8)
    groups = list(c.df[c.group_col].dropna().unique())
    for i, g in enumerate(groups):
        vals = c.df.loc[c.df[c.group_col] == g, c.metric_col].dropna().values
        if not len(vals):
            continue
        parts = ax.violinplot([vals], positions=[i], widths=0.7, showmeans=False,
                              showmedians=True, showextrema=False)
        for body in parts["bodies"]:
            body.set_facecolor(pal[i % len(pal)])
            body.set_alpha(0.55)
            body.set_edgecolor("#222")
        if c.cluster_col and c.cluster_col in c.df.columns:
            means = (c.df[c.df[c.group_col] == g]
                     .groupby(c.cluster_col)[c.metric_col].mean())
            rng = np.random.default_rng(hash(g) & 0xFFFF)
            jitter = rng.uniform(-0.12, 0.12, size=len(means))
            ax.scatter(np.full(len(means), i) + jitter, means.values,
                       s=22, color=pal[i % len(pal)], edgecolor="white",
                       linewidth=0.5, zorder=5)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([str(g) for g in groups])
    ax.set_ylabel(c.metric_col)
    return ax


def demo_shape_distribution() -> ShapeDistributionInput:
    import pandas as pd
    rng = np.random.default_rng(25)
    rows = []
    for g, mean in zip(("WT", "KO"), (1.2, 0.9)):
        for animal in range(4):
            base = mean + rng.normal(0, 0.05)
            vals = rng.normal(base, 0.15, size=25)
            rows.extend([{"g": g, "metric": v, "animal": f"{g}_{animal}"} for v in vals])
    return ShapeDistributionInput(df=pd.DataFrame(rows), metric_col="metric",
                                  group_col="g", cluster_col="animal")


def airyscan_panel_grid(ax, contract, palette: str = "okabe_ito"):
    """Draw an n-thumbnail grid inside ``ax``'s subplot spec.

    The primitive clears ``ax`` and spawns a child gridspec with one row
    holding each thumbnail, plus optional scale bar.
    """

    c = AiryscanGridInput.model_validate(contract)
    imgs = np.asarray(c.images)
    if imgs.ndim != 3:
        raise ValueError("images must be (n, h, w)")
    n = imgs.shape[0]
    cols = min(n, 4)
    rows = int(np.ceil(n / cols))
    ax.set_axis_off()
    child = GridSpecFromSubplotSpec(rows, cols, subplot_spec=ax.get_subplotspec(),
                                    hspace=0.08, wspace=0.08)
    for i in range(n):
        r, col = divmod(i, cols)
        sub = ax.figure.add_subplot(child[r, col])
        sub.imshow(imgs[i], cmap="magma")
        sub.set_xticks([]); sub.set_yticks([])
        for side in ("top", "right", "left", "bottom"):
            sub.spines[side].set_visible(False)
        if c.labels and i < len(c.labels):
            sub.text(0.02, 0.95, str(c.labels[i]), transform=sub.transAxes,
                     color="white", fontsize=7, fontweight="bold",
                     va="top", ha="left")
        if i == 0 and c.scale_length_um:
            scale_bar(sub, c.scale_length_um, color="white")
    return ax


def demo_airyscan_panel_grid() -> AiryscanGridInput:
    rng = np.random.default_rng(21)
    imgs = rng.random(size=(4, 32, 32))
    return AiryscanGridInput(images=imgs, labels=["WT", "KO", "Rescue", "Drug"],
                             scale_length_um=5.0)


def ridge_over_conditions(ax, contract, palette: str = "mechanism_class"):
    """Thin wrapper: ridge KDE per condition on the morphometry metric."""

    c = RidgeInput.model_validate(contract)
    return ridge_by_group(ax, c, palette=palette)


def demo_ridge_over_conditions() -> RidgeInput:
    import pandas as pd
    rng = np.random.default_rng(28)
    rows = []
    for cond, mean in zip(("ctrl", "cytoD", "nocoD", "blebb"), (1.0, 0.6, 0.8, 0.5)):
        rows.extend([{"g": cond, "metric": v} for v in rng.normal(mean, 0.14, size=120)])
    return RidgeInput(df=pd.DataFrame(rows), value_col="metric", group_col="g")


DEMOS = {
    "shape_distribution": (shape_distribution, demo_shape_distribution),
    "airyscan_panel_grid": (airyscan_panel_grid, demo_airyscan_panel_grid),
    "ridge_over_conditions": (ridge_over_conditions, demo_ridge_over_conditions),
}
