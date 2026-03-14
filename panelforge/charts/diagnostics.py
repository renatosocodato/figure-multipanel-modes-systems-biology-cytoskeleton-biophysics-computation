from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import auc, precision_recall_curve, roc_curve

from .base import _safe_series, create_panel_axes, RenderContext


def render_roc(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    y_true = _safe_series(ctx.data, mappings.get("group"), required=True)
    y_score = _safe_series(ctx.data, mappings.get("y"), required=True)
    y_true = pd.to_numeric(y_true, errors="coerce").fillna(0).astype(int)
    y_score = pd.to_numeric(y_score, errors="coerce")
    fpr, tpr, _ = roc_curve(y_true, y_score)
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.plot(fpr, tpr, linewidth=1.2)
    ax.plot([0, 1], [0, 1], linestyle="--", linewidth=0.8)
    ax.text(0.6, 0.2, f"AUC={auc(fpr, tpr):.3f}")
    return fig, ax


def render_pr(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    y_true = pd.to_numeric(_safe_series(ctx.data, mappings.get("group"), required=True), errors="coerce").fillna(0)
    y_score = pd.to_numeric(_safe_series(ctx.data, mappings.get("y")), errors="coerce")
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.plot(recall, precision, linewidth=1.2)
    return fig, ax


def render_calibration(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    score = pd.to_numeric(_safe_series(ctx.data, mappings.get("y")), errors="coerce")
    label = pd.to_numeric(_safe_series(ctx.data, mappings.get("group"), required=True), errors="coerce").fillna(0)
    bins = int(ctx.chart_spec.get("options", {}).get("bins", 10))
    df = pd.DataFrame({"score": score, "label": label}).dropna()
    df["bin"] = pd.qcut(df["score"], q=min(bins, len(df)), duplicates="drop")
    obs = df.groupby("bin").label.mean()
    pred = df.groupby("bin").score.mean()
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.plot(pred, obs, marker="o")
    ax.plot([0, 1], [0, 1], linestyle="--", linewidth=0.8)
    return fig, ax


def render_residuals(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    pred = pd.to_numeric(_safe_series(ctx.data, mappings.get("y")), errors="coerce")
    actual = pd.to_numeric(_safe_series(ctx.data, mappings.get("x")), errors="coerce")
    residual = actual - pred
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.scatter(pred, residual, alpha=0.7, s=12)
    return fig, ax


def render_qq(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    x = pd.to_numeric(_safe_series(ctx.data, mappings.get("x")), errors="coerce").dropna()
    n = len(x)
    q = np.linspace(0, 1, n + 2)[1:-1]
    theo = np.quantile(np.random.normal(size=n), q)
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.scatter(np.sort(x), np.sort(theo), s=8)
    lim = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]
    ax.plot(lim, lim, linestyle="--", linewidth=0.8)
    return fig, ax


def render_ma(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    m = pd.to_numeric(_safe_series(ctx.data, mappings.get("y")), errors="coerce")
    a = pd.to_numeric(_safe_series(ctx.data, mappings.get("x")), errors="coerce")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.scatter((m + a) / 2, m - a, s=10, alpha=0.6)
    return fig, ax


def render_volcano(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    x = pd.to_numeric(_safe_series(ctx.data, mappings.get("x")), errors="coerce")
    p = pd.to_numeric(_safe_series(ctx.data, mappings.get("y"), required=True), errors="coerce")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    ax.scatter(x, -np.log10(p.replace(0, np.nan)), s=8, alpha=0.6)
    return fig, ax


def render_manhattan(ctx: RenderContext, panel=None):
    mappings = ctx.chart_spec.get("mappings", {})
    chromosome = _safe_series(ctx.data, mappings.get("x"), required=True)
    p = pd.to_numeric(_safe_series(ctx.data, mappings.get("y"), required=True), errors="coerce")
    fig, ax = create_panel_axes(ctx.width, ctx.height, panel.title if panel else "", panel.subtitle if panel else "")
    # Keep positions simple/robust by ordering records and coloring by chromosome labels.
    x = pd.to_numeric(chromosome, errors="coerce").fillna(0)
    y = -np.log10(p.replace(0, np.nan))
    ax.scatter(range(len(x)), y, s=9, alpha=0.5)
    return fig, ax


def render(ctx: RenderContext, chart_type: str, panel=None):
    dispatch = {
        "roc": render_roc,
        "pr": render_pr,
        "precision_recall": render_pr,
        "calibration": render_calibration,
        "residuals": render_residuals,
        "qq": render_qq,
        "ma": render_ma,
        "volcano": render_volcano,
        "manhattan": render_manhattan,
    }
    if chart_type not in dispatch:
        raise KeyError(f"Unsupported diagnostic chart '{chart_type}'")
    return dispatch[chart_type](ctx, panel=panel)
