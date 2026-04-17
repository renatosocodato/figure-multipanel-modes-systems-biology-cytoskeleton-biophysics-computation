from __future__ import annotations


import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import gaussian_kde

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


def render_split_violin(ctx: RenderContext, panel=None):
    """Split violin by a binary grouping (e.g. sex x genotype) with animal-level overlay.

    Required mappings: x (categorical), y (numeric), group (exactly 2 levels).
    If the group column has a cardinality other than 2, the panel falls back
    to a regular (non-split) violinplot and renders a small warning pill
    rather than aborting figure generation.
    Optional options.overlay == "animal_means" + column "animal_id" overlays
    per-animal means as a stripplot.
    """
    mappings = ctx.chart_spec.get("mappings", {})
    opts = ctx.chart_spec.get("options", {})
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    palette = ctx.palette[:2] if len(ctx.palette) >= 2 else ["#D55E00", "#0072B2"]
    group_col = mappings.get("group")
    group_levels = (
        ctx.data[group_col].dropna().unique().tolist()
        if group_col and group_col in ctx.data.columns
        else []
    )
    split = len(group_levels) == 2
    if not split:
        ax.text(
            0.98, 0.98,
            f"split_violin needs 2 group levels (got {len(group_levels)}); rendering unsplit",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7, color="#991B1B",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#FEF2F2",
                  "edgecolor": "#DC2626", "linewidth": 0.6},
        )
    violin_kwargs = dict(
        data=ctx.data,
        x=mappings["x"], y=mappings["y"],
        inner=None, cut=0, linewidth=0.7, density_norm="area", ax=ax,
    )
    if split:
        violin_kwargs.update(hue=group_col, split=True, palette=palette)
    else:
        violin_kwargs["color"] = palette[0]
    sns.violinplot(**violin_kwargs)
    if opts.get("overlay") == "animal_means" and "animal_id" in ctx.data:
        grp_means = (
            ctx.data.groupby(["animal_id", mappings["x"], mappings["group"]])[mappings["y"]]
            .mean().reset_index()
        )
        sns.stripplot(
            data=grp_means, x=mappings["x"], y=mappings["y"], hue=mappings["group"],
            dodge=True, size=3, alpha=0.85, palette=palette,
            linewidth=0.4, edgecolor="white", ax=ax, legend=False,
        )
    return fig, ax


def render_ridge_distribution(ctx: RenderContext, panel=None):
    """Ridge plot: one KDE per group stacked vertically.

    Required mappings: x (numeric), group (categorical row variable).
    Optional options.bw_adjust (default 0.35), overlap (default 0.35).
    """
    mappings = ctx.chart_spec.get("mappings", {})
    opts = ctx.chart_spec.get("options", {})
    group_col = mappings.get("group")
    x_col = mappings.get("x")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    if group_col not in ctx.data or x_col not in ctx.data:
        ax.text(0.5, 0.5, "ridge requires x + group mappings",
                ha="center", va="center")
        return fig, ax
    groups = list(ctx.data[group_col].dropna().unique())
    palette = ctx.palette or ["#4C78A8"]
    x_min = float(ctx.data[x_col].quantile(0.01))
    x_max = float(ctx.data[x_col].quantile(0.99))
    if x_min == x_max:
        x_max = x_min + 1.0
    xgrid = np.linspace(x_min, x_max, 400)
    offset_step = 1.0 - float(opts.get("overlap", 0.35))
    bw = float(opts.get("bw_adjust", 0.35))
    for i, g in enumerate(groups):
        vals = ctx.data.loc[ctx.data[group_col] == g, x_col].dropna().values
        if len(vals) < 3:
            continue
        kde = gaussian_kde(vals, bw_method=bw)
        y = kde(xgrid)
        y = y / y.max() * 0.75 if y.max() > 0 else y
        base = (len(groups) - 1 - i) * offset_step
        color = palette[i % len(palette)]
        ax.fill_between(xgrid, base, base + y, color=color, alpha=0.72,
                        linewidth=0.5, edgecolor="#222")
        ax.axhline(base, color="#BBBBBB", lw=0.4, zorder=0)
        ax.text(x_min - (x_max - x_min) * 0.02, base + 0.35, str(g),
                fontsize=7.5, fontweight="bold", color=color,
                va="center", ha="right")
    ax.set_ylim(-0.2, len(groups) * offset_step + 0.3)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
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
        "split_violin": render_split_violin,
        "ridge_distribution": render_ridge_distribution,
        "dot": render_dot,
        "dot_plot": render_dot,
    }
    if chart_type not in renderers:
        raise KeyError(f"Unsupported univariate chart type '{chart_type}'")
    return renderers[chart_type](ctx, panel=panel)

