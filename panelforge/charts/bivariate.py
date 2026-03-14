from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import scipy.stats as st
import seaborn as sns
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt

from .base import _safe_series, create_panel_axes, RenderContext


def render_scatter(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(ctx.data, mappings.get("x"))
    y = _safe_series(ctx.data, mappings.get("y"))
    group_key = mappings.get("group")
    legend_handles = []
    color_codes: np.ndarray | None = None
    categories: np.ndarray | None = None
    color_values = None

    if isinstance(group_key, str) and group_key in ctx.data:
        raw_group = ctx.data[group_key]
        if pd.api.types.is_numeric_dtype(raw_group):
            color_values = raw_group.to_numpy(dtype=float)
            palette_name = "viridis"
        else:
            color_codes, categories = pd.factorize(raw_group, sort=True)
            color_values = color_codes
            palette_name = "tab10"
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if color_values is not None:
        if color_codes is None:
            ax.scatter(x, y, c=color_values, alpha=0.8, s=10, cmap=palette_name)
        else:
            palette = plt.get_cmap(palette_name)
            ax.scatter(x, y, c=color_values, alpha=0.8, s=10, cmap=palette_name)
            if categories is None:
                categories = []
            for code, category in enumerate(categories):
                legend_handles.append(Line2D([0], [0], marker="o", linestyle="none", color=palette(code), label=str(category)))
            if legend_handles:
                ax.legend(handles=legend_handles, fontsize=7, frameon=True)
    else:
        ax.scatter(x, y, alpha=0.8, s=10)
    return fig, ax


def render_line(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(ctx.data, mappings.get("x"))
    y = _safe_series(ctx.data, mappings.get("y"))
    c = mappings.get("group")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if c and c in ctx.data:
        for _, sub in ctx.data.groupby(c):
            ax.plot(sub[x.name], sub[y.name], linewidth=1.2)
    else:
        ax.plot(x, y, linewidth=1.2)
    return fig, ax


def render_area(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(ctx.data, mappings.get("x"))
    y = _safe_series(ctx.data, mappings.get("y"))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.fill_between(x, 0, y, alpha=0.35)
    ax.plot(x, y, linewidth=1.2)
    return fig, ax


def render_stacked_area(ctx: RenderContext, panel=None):
    data = ctx.data
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(data, mappings.get("x"))
    cols = mappings.get("facets") or []
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if cols:
        arr = data[cols].to_numpy(dtype=float)
        ax.stackplot(x, arr.T, labels=cols)
        ax.legend(fontsize=7)
    return fig, ax


def render_regression_ci(ctx: RenderContext, panel=None):
    data = ctx.data
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(data, mappings.get("x"))
    y = _safe_series(data, mappings.get("y"))
    xx = x.to_numpy(dtype=float)
    yy = y.to_numpy(dtype=float)
    finite = np.isfinite(xx) & np.isfinite(yy)
    xx = xx[finite]
    yy = yy[finite]
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if len(xx) >= 2:
        slope, intercept, r_val, p_val, std_err = st.linregress(xx, yy)
        x_hat = np.linspace(xx.min(), xx.max(), 100)
        y_hat = slope * x_hat + intercept
        ax.scatter(xx, yy, alpha=0.6, s=8)
        ax.plot(x_hat, y_hat, linewidth=1.4)
        ax.text(0.02, 0.95, f"R2={r_val ** 2:.2f} p={p_val:.2e}", transform=ax.transAxes, fontsize=8)
    return fig, ax


def render_hexbin(ctx: RenderContext, panel=None):
    data = ctx.data
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(data, mappings.get("x"))
    y = _safe_series(data, mappings.get("y"))
    gridsize = int(ctx.chart_spec.get("options", {}).get("gridsize", 30))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.hexbin(x, y, gridsize=gridsize, cmap="Blues")
    return fig, ax


def render_correlogram(ctx: RenderContext, panel=None):
    data = ctx.data
    num = data.select_dtypes("number")
    corr = num.corr()
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    sns.heatmap(corr, annot=False, cmap="coolwarm", ax=ax)
    return fig, ax


def render(ctx: RenderContext, chart_type: str, panel=None):
    dispatch = {
        "scatter": render_scatter,
        "line": render_line,
        "area": render_area,
        "stacked_area": render_stacked_area,
        "regression_ci": render_regression_ci,
        "regression": render_regression_ci,
        "hexbin": render_hexbin,
        "correlogram": render_correlogram,
    }
    if chart_type not in dispatch:
        raise KeyError(f"Unsupported bivariate chart '{chart_type}'")
    return dispatch[chart_type](ctx, panel=panel)
