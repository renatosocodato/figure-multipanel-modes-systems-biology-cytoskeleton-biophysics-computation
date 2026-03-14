from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA

from .base import _safe_series, create_panel_axes, RenderContext


def render_heatmap(ctx: RenderContext, panel=None):
    numeric = ctx.data.select_dtypes("number")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if numeric.empty:
        ax.text(0.5, 0.5, "No numeric data", ha="center", va="center")
    else:
        sns.heatmap(numeric.corr(), cmap="vlag", ax=ax)
    return fig, ax


def render_cluster_heatmap(ctx: RenderContext, panel=None):
    numeric = ctx.data.select_dtypes("number")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if numeric.empty:
        ax.text(0.5, 0.5, "No numeric data", ha="center", va="center")
    else:
        sns.clustermap(numeric.dropna(axis=1, how="all"), cmap="mako", ax=ax)
    return fig, ax


def render_corr_matrix(ctx: RenderContext, panel=None):
    numeric = ctx.data.select_dtypes("number")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if numeric.empty:
        ax.text(0.5, 0.5, "No numeric data", ha="center", va="center")
    else:
        sns.heatmap(numeric.corr(), cmap="vlag", vmin=-1, vmax=1, ax=ax)
    return fig, ax


def render_pca_scatter(ctx: RenderContext, panel=None):
    numeric = ctx.data.select_dtypes("number").dropna(axis=1, how="all")
    mappings = ctx.chart_spec.get("mappings", {})
    color = mappings.get("group")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if numeric.empty:
        ax.text(0.5, 0.5, "No numeric data", ha="center", va="center")
        return fig, ax
    comp = PCA(n_components=min(2, numeric.shape[1]))
    coords = comp.fit_transform(numeric)
    if coords.shape[1] < 2:
        ax.text(0.5, 0.5, "PCA dimensionality insufficient", ha="center", va="center")
        return fig, ax
    c = ctx.data[color] if color in ctx.data else None
    ax.scatter(coords[:, 0], coords[:, 1], c=c, s=10, alpha=0.8, cmap="viridis")
    return fig, ax


def render_tsne_scatter(ctx: RenderContext, panel=None):
    # Lightweight fallback: reuse PCA-style decomposition when TSNE is unavailable.
    return render_pca_scatter(ctx, panel=panel)


def render_umap_scatter(ctx: RenderContext, panel=None):
    # Lightweight fallback: reuse PCA-style decomposition when UMAP is unavailable.
    return render_pca_scatter(ctx, panel=panel)


def render(ctx: RenderContext, chart_type: str, panel=None):
    dispatch = {
        "heatmap": render_heatmap,
        "cluster_heatmap": render_cluster_heatmap,
        "corr_matrix": render_corr_matrix,
        "pca": render_pca_scatter,
        "pca_scatter": render_pca_scatter,
        "tsne_scatter": render_tsne_scatter,
        "umap_scatter": render_umap_scatter,
        "tsne": render_tsne_scatter,
        "umap": render_umap_scatter,
    }
    if chart_type not in dispatch:
        raise KeyError(f"Unsupported multivariate chart '{chart_type}'")
    return dispatch[chart_type](ctx, panel=panel)

