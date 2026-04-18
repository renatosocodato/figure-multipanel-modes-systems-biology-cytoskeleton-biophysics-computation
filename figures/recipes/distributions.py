"""Distribution-comparison recipes.

Contains:
    split_violin           — binary-hue split with animal-level overlay
    ridge_by_group         — vertical KDE stack with row labels
    beeswarm_by_group      — categorical scatter with mean/median overlays
    ecdf_by_group          — empirical CDFs per group
    histogram_by_group     — stacked/overlaid histograms with optional KDE
    paired_slopes          — before/after line plot for paired observations
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

from ..core.contract import (
    DistributionByGroupInput,
    PairedSlopesInput,
    RidgeInput,
)
from ..core.palette import get_palette
from ..core.primitives import callout_box, iter_palette


def _positions(df: pd.DataFrame, group_col: str) -> tuple[list, dict[object, int]]:
    levels = list(df[group_col].dropna().unique())
    return levels, {level: idx for idx, level in enumerate(levels)}


def _is_degenerate(values: np.ndarray) -> bool:
    """True when KDE would hit a singular-covariance error.

    Two independent checks: (1) variance below a tight floor — catches exact
    duplicates after rounding; (2) peak-to-peak zero — catches exact identity.
    """

    if len(values) < 3:
        return True
    if float(np.ptp(values)) <= 0.0:
        return True
    return float(np.var(values)) <= 1e-18


def split_violin(ax, contract, palette: str = "sex_x_genotype"):
    """Violin halves per binary ``hue_col`` grouped on ``group_col``."""

    c = DistributionByGroupInput.model_validate(contract)
    pal = get_palette(palette).categorical
    if c.hue_col is None or c.hue_col not in c.df.columns:
        raise ValueError("split_violin requires hue_col with exactly 2 levels")
    hues = list(c.df[c.hue_col].dropna().unique())
    if len(hues) != 2:
        raise ValueError(f"split_violin needs 2 hue levels; got {len(hues)}")
    groups, pos = _positions(c.df, c.group_col)
    left_vals, right_vals = [], []
    for g in groups:
        left_vals.append(c.df.loc[(c.df[c.group_col] == g) & (c.df[c.hue_col] == hues[0]), c.value_col].dropna().values)
        right_vals.append(c.df.loc[(c.df[c.group_col] == g) & (c.df[c.hue_col] == hues[1]), c.value_col].dropna().values)
    width = 0.38
    for i, (lv, rv) in enumerate(zip(left_vals, right_vals)):
        for side, vals, col in (("left", lv, pal[0]), ("right", rv, pal[1])):
            if len(vals) == 0:
                continue
            if _is_degenerate(vals):
                # Zero-variance cohort (e.g., all rounded to the same value) —
                # gaussian_kde would raise on singular covariance. Fall back to
                # a thin horizontal tick at the constant value so the cohort is
                # still represented in the panel.
                y_const = float(vals[0])
                left_edge = i - width if side == "left" else i
                right_edge = i if side == "left" else i + width
                ax.hlines(y_const, left_edge, right_edge, color=col,
                          linewidth=1.2, alpha=0.9)
                continue
            kde = gaussian_kde(vals)
            ys = np.linspace(vals.min(), vals.max(), 128)
            xs = kde(ys)
            xs = xs / xs.max() * width
            if side == "left":
                ax.fill_betweenx(ys, i - xs, i, color=col, alpha=0.75, linewidth=0.5, edgecolor="#222")
            else:
                ax.fill_betweenx(ys, i, i + xs, color=col, alpha=0.75, linewidth=0.5, edgecolor="#222")
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([str(g) for g in groups])
    ax.set_ylabel(c.value_col)
    callout_box(ax, 0.02, 0.98, f"hues: {hues[0]} / {hues[1]}", ha="left", va="top",
                color="#333333")
    if c.overlay == "animal_means" and c.cluster_col and c.cluster_col in c.df.columns:
        means = (c.df.groupby([c.cluster_col, c.group_col, c.hue_col])[c.value_col]
                 .mean().reset_index())
        for _, row in means.iterrows():
            side = -width / 2 if row[c.hue_col] == hues[0] else width / 2
            col = pal[0] if row[c.hue_col] == hues[0] else pal[1]
            ax.scatter(pos[row[c.group_col]] + side, row[c.value_col],
                       s=16, color=col, edgecolor="white", linewidth=0.4, zorder=5)
    return ax


def demo_split_violin() -> DistributionByGroupInput:
    rng = np.random.default_rng(11)
    rows = []
    for sex, shift in (("F", 0.0), ("M", 0.08)):
        for geno in ("WT", "KO"):
            base = 0.40 + (0.10 if geno == "KO" else 0.0) + (shift if geno == "KO" else 0)
            animals = [f"{sex}{geno}_{i}" for i in range(3)]
            for a in animals:
                vals = rng.normal(base, 0.05, size=10)
                rows.extend([{"sex": sex, "geno": geno, "animal": a, "cv": v} for v in vals])
    df = pd.DataFrame(rows)
    return DistributionByGroupInput(df=df, value_col="cv", group_col="geno",
                                    hue_col="sex", cluster_col="animal",
                                    overlay="animal_means")


def ridge_by_group(ax, contract, palette: str = "okabe_ito"):
    """Stack one KDE ridge per group with overlap control."""

    c = RidgeInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 12)
    groups = list(c.df[c.group_col].dropna().unique())
    x_min = float(c.df[c.value_col].quantile(0.02))
    x_max = float(c.df[c.value_col].quantile(0.98))
    if x_max <= x_min:
        x_max = x_min + 1.0
    xgrid = np.linspace(x_min, x_max, 400)
    offset_step = 1.0 - float(c.overlap)
    for i, g in enumerate(groups):
        vals = c.df.loc[c.df[c.group_col] == g, c.value_col].dropna().values
        base = (len(groups) - 1 - i) * offset_step
        col = pal[i % len(pal)]
        if len(vals) == 0:
            continue
        if _is_degenerate(vals):
            # Degenerate (constant) cohort — render a single vertical spike at
            # the shared value so the row still appears.
            ax.vlines(float(vals[0]), base, base + 0.75, color=col, linewidth=1.3,
                      alpha=0.9)
        else:
            kde = gaussian_kde(vals, bw_method=float(c.bw_adjust))
            y = kde(xgrid)
            y = (y / y.max() * 0.75) if y.max() > 0 else y
            ax.fill_between(xgrid, base, base + y, color=col, alpha=0.75,
                            linewidth=0.5, edgecolor="#222")
        ax.axhline(base, color="#BBBBBB", linewidth=0.4, zorder=0)
        ax.text(x_min - (x_max - x_min) * 0.015, base + 0.35, str(g),
                fontsize=7.5, fontweight="bold", color=col, va="center", ha="right")
    ax.set_xlabel(c.value_col)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    return ax


def demo_ridge_by_group() -> RidgeInput:
    rng = np.random.default_rng(4)
    rows = []
    for g, mean in zip(("F_WT", "F_KO", "M_WT", "M_KO"), (0.40, 0.55, 0.48, 0.35)):
        rows.extend([{"g": g, "v": v} for v in rng.normal(mean, 0.06, size=120)])
    return RidgeInput(df=pd.DataFrame(rows), value_col="v", group_col="g")


def beeswarm_by_group(ax, contract, palette: str = "okabe_ito"):
    """Categorical scatter with jitter + mean marker."""

    c = DistributionByGroupInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 12)
    groups, _ = _positions(c.df, c.group_col)
    rng = np.random.default_rng(0)
    for i, g in enumerate(groups):
        vals = c.df.loc[c.df[c.group_col] == g, c.value_col].dropna().values
        jitter = rng.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals, s=10, alpha=0.65,
                   color=pal[i % len(pal)], edgecolor="white", linewidth=0.3)
        if len(vals):
            ax.hlines(float(np.mean(vals)), i - 0.28, i + 0.28, color="#111", linewidth=1.2)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([str(g) for g in groups])
    ax.set_ylabel(c.value_col)
    return ax


def demo_beeswarm_by_group() -> DistributionByGroupInput:
    rng = np.random.default_rng(12)
    rows = []
    for g, m in zip(("ctrl", "drug1", "drug2"), (0.5, 0.35, 0.6)):
        rows.extend([{"g": g, "y": v} for v in rng.normal(m, 0.09, size=50)])
    return DistributionByGroupInput(df=pd.DataFrame(rows), value_col="y", group_col="g")


def ecdf_by_group(ax, contract, palette: str = "okabe_ito"):
    """ECDF line per group."""

    c = DistributionByGroupInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 12)
    groups, _ = _positions(c.df, c.group_col)
    for i, g in enumerate(groups):
        vals = np.sort(c.df.loc[c.df[c.group_col] == g, c.value_col].dropna().values)
        if not len(vals):
            continue
        ys = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, ys, color=pal[i % len(pal)], linewidth=1.4, label=str(g))
    ax.set_xlabel(c.value_col)
    ax.set_ylabel("F(x)")
    ax.legend(fontsize=7.5, frameon=False)
    return ax


def demo_ecdf_by_group() -> DistributionByGroupInput:
    return demo_beeswarm_by_group()


def histogram_by_group(ax, contract, palette: str = "okabe_ito", *, bins: int = 30):
    """Overlaid histograms with step outlines per group."""

    c = DistributionByGroupInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 12)
    groups, _ = _positions(c.df, c.group_col)
    all_vals = c.df[c.value_col].dropna().values
    edges = np.histogram_bin_edges(all_vals, bins=bins)
    for i, g in enumerate(groups):
        vals = c.df.loc[c.df[c.group_col] == g, c.value_col].dropna().values
        col = pal[i % len(pal)]
        ax.hist(vals, bins=edges, alpha=0.32, color=col, histtype="stepfilled",
                edgecolor=col, linewidth=1.0, label=str(g))
    ax.set_xlabel(c.value_col)
    ax.set_ylabel("count")
    ax.legend(fontsize=7.5, frameon=False)
    return ax


def demo_histogram_by_group() -> DistributionByGroupInput:
    return demo_beeswarm_by_group()


def paired_slopes(ax, contract, palette: str = "okabe_ito"):
    """Before/after line per subject with mean markers."""

    c = PairedSlopesInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 4)
    conds = list(c.df[c.condition_col].dropna().unique())
    if len(conds) < 2:
        raise ValueError("paired_slopes needs at least 2 condition levels")
    wide = c.df.pivot_table(index=c.subject_col, columns=c.condition_col,
                            values=c.value_col, aggfunc="mean")
    for i in range(len(conds) - 1):
        left = wide[conds[i]].values
        right = wide[conds[i + 1]].values
        for s in range(len(left)):
            ax.plot([i, i + 1], [left[s], right[s]], color=pal[0], alpha=0.4, linewidth=0.9)
        ax.scatter([i] * len(left), left, s=16, color=pal[0], edgecolor="white", linewidth=0.4, zorder=4)
        ax.scatter([i + 1] * len(right), right, s=16, color=pal[1], edgecolor="white", linewidth=0.4, zorder=4)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([str(c) for c in conds])
    ax.set_ylabel(c.value_col)
    return ax


def demo_paired_slopes() -> PairedSlopesInput:
    rng = np.random.default_rng(5)
    subs = [f"s{i}" for i in range(12)]
    rows = []
    for s in subs:
        base = rng.normal(1.0, 0.15)
        rows.append({"subj": s, "cond": "pre", "v": base})
        rows.append({"subj": s, "cond": "post", "v": base + rng.normal(0.3, 0.1)})
    return PairedSlopesInput(df=pd.DataFrame(rows), subject_col="subj",
                             condition_col="cond", value_col="v")


DEMOS = {
    "split_violin": (split_violin, demo_split_violin),
    "ridge_by_group": (ridge_by_group, demo_ridge_by_group),
    "beeswarm_by_group": (beeswarm_by_group, demo_beeswarm_by_group),
    "ecdf_by_group": (ecdf_by_group, demo_ecdf_by_group),
    "histogram_by_group": (histogram_by_group, demo_histogram_by_group),
    "paired_slopes": (paired_slopes, demo_paired_slopes),
}
