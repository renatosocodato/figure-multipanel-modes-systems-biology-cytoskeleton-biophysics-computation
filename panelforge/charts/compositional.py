from __future__ import annotations


import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import colormaps

from .base import _safe_series, create_panel_axes, RenderContext


def render_stacked_bar(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    category = _safe_series(ctx.data, mappings.get("category"), required=True)
    value = _safe_series(ctx.data, mappings.get("y"), required=True)
    group = mappings.get("group")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    table = pd.DataFrame({"category": category, "value": value})
    if group and group in ctx.data:
        table["group"] = ctx.data[group]
        data = table.pivot_table(index="category", columns="group", values="value", aggfunc="sum", fill_value=0)
        data.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
    else:
        table.groupby("category")["value"].sum().plot(kind="bar", stacked=True, ax=ax)
    return fig, ax


def render_stacked_bar_100(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    category = _safe_series(ctx.data, mappings.get("category"), required=True)
    value = _safe_series(ctx.data, mappings.get("y"), required=True)
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    table = pd.DataFrame({"category": category, "value": value})
    prop = table.groupby("category")["value"].sum()
    prop = prop / prop.sum() if prop.sum() else prop
    prop.plot(kind="bar", stacked=True, ax=ax)
    return fig, ax


def render_outcome_composition(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    outcome = _safe_series(ctx.data, mappings.get("category"), required=True)
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    outcome.value_counts().plot(kind="bar", ax=ax)
    return fig, ax


def render_tally_tiles(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    tile_col = mappings.get("category")
    if tile_col not in ctx.data:
        tile_col = mappings.get("x")
    if tile_col is None or tile_col not in ctx.data:
        return create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    counts = ctx.data[tile_col].value_counts().reset_index()
    counts.columns = [tile_col, "count"]
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    sns.heatmap(
        counts[["count"]].T,
        annot=counts[["count"]].T,
        fmt="d",
        cmap="Greens",
        cbar=False,
        ax=ax,
    )
    return fig, ax


def render_sobol_bar(ctx: RenderContext, panel=None):
    """Horizontal bar chart for Sobol first- or total-order indices with CI whiskers.

    Required mappings: category (parameter name), y (S1 or ST), yerr (CI).
    Optional options.order = "descending" (default) / "ascending";
              options.cmap ("viridis" default) maps bar colors by value.
    """
    mappings = ctx.chart_spec.get("mappings", {})
    opts = ctx.chart_spec.get("options", {})
    cat_col = mappings.get("category")
    y_col = mappings.get("y")
    err_col = mappings.get("yerr")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if cat_col not in ctx.data or y_col not in ctx.data:
        ax.text(0.5, 0.5, "sobol_bar requires category + y mappings",
                ha="center", va="center")
        return fig, ax
    df = ctx.data.copy()
    ascending = opts.get("order", "descending") != "descending"
    df = df.sort_values(y_col, ascending=ascending)
    cmap_name = opts.get("cmap", "viridis")
    cmap = colormaps[cmap_name]
    colors = cmap(np.linspace(0.18, 0.85, len(df)))
    yerr = df[err_col].to_numpy() if err_col in df.columns else None
    bars = ax.barh(df[cat_col].astype(str), df[y_col].astype(float),
                   xerr=yerr, color=colors,
                   edgecolor="#222", linewidth=0.5,
                   error_kw=dict(ecolor="#333", lw=0.7, capsize=2))
    # Value labels: 3 decimals below 0.01, else 2
    for bar, v in zip(bars, df[y_col].astype(float)):
        text = f"{v:.3f}" if v < 0.01 else f"{v:.2f}"
        pad = (yerr[list(df.index).index(bar.get_y())] if yerr is not None and bar.get_y() in list(df.index) else 0) + 0.01
        ax.text(v + float(pad), bar.get_y() + bar.get_height() / 2,
                text, va="center", fontsize=7, color="#222")
    ax.set_xlim(0, float(df[y_col].max()) * 1.30)
    return fig, ax


def render(ctx: RenderContext, chart_type: str, panel=None):
    dispatch = {
        "stacked_bar": render_stacked_bar,
        "stacked_bar_100": render_stacked_bar_100,
        "outcome_composition": render_outcome_composition,
        "tally_tiles": render_tally_tiles,
        "sobol_bar": render_sobol_bar,
    }
    if chart_type not in dispatch:
        raise KeyError(f"Unsupported compositional chart '{chart_type}'")
    return dispatch[chart_type](ctx, panel=panel)

