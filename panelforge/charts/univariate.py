from __future__ import annotations


import pandas as pd
import seaborn as sns

from .base import _safe_series, create_panel_axes, RenderContext


def render_bar(ctx: RenderContext, panel=None):
    spec = ctx.chart_spec
    mappings = spec.get("mappings", {})
    x = _safe_series(ctx.data, mappings.get("x"))
    y = _safe_series(ctx.data, mappings.get("y"))
    color = mappings.get("group")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if color and color in ctx.data:
        sns.barplot(x=x, y=y, hue=ctx.data[color], ax=ax, palette=ctx.palette)
    else:
        sns.barplot(x=x, y=y, ax=ax, color=ctx.palette[0] if ctx.palette else "#4C78A8")
    return fig, ax


def render_lollipop(ctx: RenderContext, panel=None):
    data = ctx.data
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(data, mappings.get("x"))
    y = _safe_series(data, mappings.get("y"))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.stem(x, y, linefmt=ctx.palette[0] if ctx.palette else "#4C78A8", markerfmt="o", basefmt="")
    return fig, ax


def render_hist(ctx: RenderContext, panel=None):
    data = _safe_series(ctx.data, ctx.chart_spec.get("mappings", {}).get("x"))
    bins = int(ctx.chart_spec.get("options", {}).get("bins", 30))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.hist(data.dropna(), bins=bins, color=ctx.palette[0] if ctx.palette else "#4C78A8")
    return fig, ax


def render_kde(ctx: RenderContext, panel=None):
    data = _safe_series(ctx.data, ctx.chart_spec.get("mappings", {}).get("x"))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    sns.kdeplot(data=data.dropna(), ax=ax, color=ctx.palette[0] if ctx.palette else "#4C78A8", fill=True)
    return fig, ax


def render_ecdf(ctx: RenderContext, panel=None):
    data = _safe_series(ctx.data, ctx.chart_spec.get("mappings", {}).get("x"))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    sorted_y = pd.Series(data).dropna().sort_values().reset_index(drop=True)
    if len(sorted_y):
        y = (sorted_y.index + 1) / len(sorted_y)
        ax.plot(sorted_y, y, linewidth=1.5, color=ctx.palette[0] if ctx.palette else "#4C78A8")
    return fig, ax


def render_box(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(ctx.data, mappings.get("x"))
    y = _safe_series(ctx.data, mappings.get("y"))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if mappings.get("group") and mappings.get("group") in ctx.data:
        sns.boxplot(x=ctx.data[mappings["x"]], y=ctx.data[mappings["y"]], hue=ctx.data[mappings["group"]], ax=ax, palette=ctx.palette)
    else:
        ax.boxplot(pd.DataFrame({"y": y, "x": x}).dropna().groupby(x, dropna=False).apply(lambda g: g["y"]))
    return fig, ax


def render_violin(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(ctx.data, mappings.get("x"))
    y = _safe_series(ctx.data, mappings.get("y"))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    sns.violinplot(x=x, y=y, hue=mappings.get("group") if mappings.get("group") in ctx.data else None, data=ctx.data, ax=ax, palette=ctx.palette)
    return fig, ax


def render_dot(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    x = _safe_series(ctx.data, mappings.get("x"))
    y = _safe_series(ctx.data, mappings.get("y"))
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.scatter(x, y, s=20, alpha=0.75, color=ctx.palette[0] if ctx.palette else "#4C78A8")
    return fig, ax


def render(ctx: RenderContext, chart_type: str, panel=None):
    renderers = {
        "bar": render_bar,
        "lollipop": render_lollipop,
        "hist": render_hist,
        "kde": render_kde,
        "ecdf": render_ecdf,
        "box": render_box,
        "violin": render_violin,
        "dot": render_dot,
        "dot_plot": render_dot,
    }
    if chart_type not in renderers:
        raise KeyError(f"Unsupported univariate chart type '{chart_type}'")
    return renderers[chart_type](ctx, panel=panel)

