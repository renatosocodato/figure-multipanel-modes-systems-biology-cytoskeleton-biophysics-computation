from __future__ import annotations


import numpy as np
import pandas as pd
import scipy.stats as st
import seaborn as sns
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
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


def render_phase_portrait(ctx: RenderContext, panel=None):
    """2D ODE phase portrait: contour backdrop + gradient streamplot + fixed points.

    Reads `options.rhs` as a key into `panelforge.dynamics.RHS_REGISTRY` for
    the vector field, and `options.potential` as an independent key into
    `POTENTIAL_REGISTRY` for the contour backdrop. `potential` defaults to
    `rhs` when omitted, and the key sentinel `false`/`null`/`"none"`
    disables the backdrop entirely. Fixed points come from the `data`
    frame. Coordinate columns are resolved through `mappings.x`/
    `mappings.y` (defaulting to "x" / "y"); the per-state label column is
    `mappings.category` (falling back to "state" or "category"); optional
    `stability` column drives the stable/unstable marker style. Labels are
    halo'd for legibility.
    """
    from ..dynamics import RHS_REGISTRY, POTENTIAL_REGISTRY

    mappings = ctx.chart_spec.get("mappings", {})
    x_col = mappings.get("x") or "x"
    y_col = mappings.get("y") or "y"
    cat_col = mappings.get("category")
    opts = ctx.chart_spec.get("options", {})
    xlim = opts.get("xlim", [0.0, 3.0])
    ylim = opts.get("ylim", [0.0, 3.0])
    grid = int(opts.get("grid", 30))
    rhs_key = opts.get("rhs")
    cond = opts.get("cond", "basal")
    # `potential` defaults to the RHS key; explicit false/null/"none" disables
    # the backdrop even when the RHS does have a registered potential.
    if "potential" in opts:
        raw_potential = opts["potential"]
        if raw_potential is False or raw_potential is None or (
            isinstance(raw_potential, str) and raw_potential.lower() in {"", "none", "off"}
        ):
            potential_key = None
        else:
            potential_key = str(raw_potential)
    else:
        potential_key = rhs_key

    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")

    if rhs_key not in RHS_REGISTRY:
        ax.text(0.5, 0.5, f"unknown RHS: {rhs_key}", ha="center", va="center")
        return fig, ax
    f = RHS_REGISTRY[rhs_key]

    # Contour backdrop from the configured potential (if registered).
    if potential_key and potential_key in POTENTIAL_REGISTRY:
        U_fn = POTENTIAL_REGISTRY[potential_key]
        xg = np.linspace(xlim[0] + 1e-3, xlim[1], 200)
        yg = np.linspace(ylim[0] + 1e-3, ylim[1], 200)
        XX, YY = np.meshgrid(xg, yg)
        # 2D extension: U_2D = U(x) + 0.5*lam*(x-y)^2
        lam = float(opts.get("confinement", 0.45))
        UU = U_fn(XX, cond) + 0.5 * lam * (XX - YY)**2
        lo, hi = np.percentile(UU, 3), np.percentile(UU, 85)
        ax.contourf(XX, YY, np.clip(UU, lo, hi),
                    levels=20, cmap="Blues_r", alpha=0.35, zorder=0)
        ax.contour(XX, YY, UU, levels=np.linspace(lo, hi, 9),
                   colors="#7A8AA3", linewidths=0.45, alpha=0.55, zorder=1)

    # Streamplot from coupled 2D gradient dynamics
    xx, yy = np.meshgrid(np.linspace(xlim[0] + 0.05, xlim[1] - 0.05, grid),
                         np.linspace(ylim[0] + 0.05, ylim[1] - 0.05, grid))
    U_grid = np.zeros_like(xx)
    V_grid = np.zeros_like(yy)
    for i in range(grid):
        for j in range(grid):
            dx, dy = f([xx[i, j], yy[i, j]], cond) if _supports_cond(f) else f([xx[i, j], yy[i, j]])
            U_grid[i, j], V_grid[i, j] = dx, dy
    speed = np.sqrt(U_grid**2 + V_grid**2)
    ax.streamplot(xx, yy, U_grid, V_grid,
                  color=np.log1p(speed), cmap="viridis",
                  density=1.15, linewidth=0.6, arrowsize=0.75, zorder=2)

    # Slow manifold (identity line) if requested
    if opts.get("nullclines", True):
        ax.plot(xlim, ylim, color="#009E73", lw=1.3, ls="--", alpha=0.9, zorder=3)

    # Fixed points from the data mapping
    halo = [pe.withStroke(linewidth=2.8, foreground="white")]
    fp_palette = opts.get("fp_palette", {"home": "#2E7D32", "gate": "#F9A825", "trap": "#C62828"})
    have_xy = x_col in ctx.data.columns and y_col in ctx.data.columns
    label_sources = [cat_col] if cat_col else []
    label_sources.extend(["state", "category"])
    if have_xy:
        for _, row in ctx.data.iterrows():
            name_raw = ""
            for src in label_sources:
                if src and src in row and pd.notna(row[src]):
                    name_raw = str(row[src]).strip()
                    break
            name_key = name_raw.lower().split("_")[0]
            col = fp_palette.get(name_key, "#111111")
            stability = str(row.get("stability", "stable")).lower()
            xv, yv = row[x_col], row[y_col]
            if stability == "stable":
                ax.plot(xv, yv, "o", mfc=col, mec="black",
                        mew=0.9, ms=9, zorder=6)
                if name_raw:
                    ax.annotate(name_raw.upper(), (xv, yv),
                                xytext=(10, 8), textcoords="offset points",
                                fontsize=9, fontweight="bold", color=col,
                                path_effects=halo, zorder=7)
            else:
                ax.plot(xv, yv, "x", color="#111", ms=8, mew=1.7,
                        zorder=6, path_effects=halo)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    return fig, ax


def _supports_cond(fn) -> bool:
    try:
        from inspect import signature
        return "cond" in signature(fn).parameters
    except (ValueError, TypeError):
        return False


def render_hierarchical_ci_line(ctx: RenderContext, panel=None):
    """Timecourse with hierarchical (cluster-level) 95% CI band.

    Required mappings: x, y, group; options.cluster names the clustering column
    (typically "animal_id"). Between-cluster SEM yields a 95 % CI that respects
    the nested design rather than treating cells as independent observations.
    """
    mappings = ctx.chart_spec.get("mappings", {})
    opts = ctx.chart_spec.get("options", {})
    cluster_col = opts.get("cluster", "animal_id")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    palette = ctx.palette or ["#0072B2", "#D55E00", "#009E73"]
    for i, (g, sub) in enumerate(ctx.data.groupby(mappings["group"])):
        if cluster_col not in sub.columns:
            continue
        clusters = sub.groupby([cluster_col, mappings["x"]])[mappings["y"]].mean().unstack(cluster_col)
        t = clusters.index.to_numpy()
        mean = clusters.mean(axis=1).to_numpy()
        # SEM per x-bin uses the observed cluster count at that bin, not the
        # total cluster column count — clusters can be missing at some x
        # values (partial coverage), in which case dividing by the full width
        # underestimates uncertainty. NaN counts (<2) yield NaN SEM so the
        # band drops out rather than collapsing to zero.
        counts = clusters.count(axis=1).to_numpy()
        std = clusters.std(axis=1, ddof=1).to_numpy()
        with np.errstate(divide="ignore", invalid="ignore"):
            sem = np.where(counts >= 2, std / np.sqrt(counts), np.nan)
        lo = mean - 1.96 * sem
        hi = mean + 1.96 * sem
        color = palette[i % len(palette)]
        ax.fill_between(t, lo, hi, color=color, alpha=0.20, linewidth=0)
        ax.plot(t, mean, color=color, lw=1.8, label=str(g))
    ax.legend(fontsize=7.5, frameon=False)
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
        "phase_portrait": render_phase_portrait,
        "hierarchical_ci_line": render_hierarchical_ci_line,
    }
    if chart_type not in dispatch:
        raise KeyError(f"Unsupported bivariate chart '{chart_type}'")
    return dispatch[chart_type](ctx, panel=panel)
