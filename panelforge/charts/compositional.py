from __future__ import annotations


import pandas as pd
import seaborn as sns

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


def render(ctx: RenderContext, chart_type: str, panel=None):
    dispatch = {
        "stacked_bar": render_stacked_bar,
        "stacked_bar_100": render_stacked_bar_100,
        "outcome_composition": render_outcome_composition,
        "tally_tiles": render_tally_tiles,
    }
    if chart_type not in dispatch:
        raise KeyError(f"Unsupported compositional chart '{chart_type}'")
    return dispatch[chart_type](ctx, panel=panel)

