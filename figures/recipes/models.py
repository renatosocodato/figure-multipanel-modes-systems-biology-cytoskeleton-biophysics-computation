"""Regression / mixed-effects recipes.

Contains:
    coef_forest                    — terms vs estimates with CIs and labels
    partial_dependence             — PDP with optional ICE lines
    random_effects_caterpillar     — shrinkage plot for per-cluster intercepts
"""
from __future__ import annotations

import numpy as np

from ..core.contract import (
    CoefForestInput,
    PartialDependenceInput,
    RandomEffectsInput,
)
from ..core.palette import get_palette
from ..core.primitives import dashed_reference, iter_palette, right_of_ci_label, smart_fmt


def coef_forest(ax, contract, palette: str = "okabe_ito"):
    """Horizontal forest plot with right-of-CI value labels."""

    c = CoefForestInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 4)
    y = np.arange(len(c.terms))
    est = np.asarray(c.estimate); lo = np.asarray(c.ci_lo); hi = np.asarray(c.ci_hi)
    highlight = set(c.highlight or [])
    for i, term in enumerate(c.terms):
        color = pal[2 % len(pal)] if term in highlight else pal[0]
        ax.hlines(i, lo[i], hi[i], color=color, linewidth=1.3)
        ax.scatter(est[i], i, color=color, s=28, zorder=5, edgecolor="white", linewidth=0.6)
        right_of_ci_label(ax, upper=hi[i], y=i, text=smart_fmt(est[i]),
                          color=color)
    ax.set_yticks(y)
    ax.set_yticklabels(c.terms, fontsize=8)
    ax.invert_yaxis()
    dashed_reference(ax, c.reference, axis="x")
    ax.set_xlabel("estimate")
    return ax


def demo_coef_forest() -> CoefForestInput:
    terms = ["Intercept", "sex_M", "geno_KO", "sex_M×geno_KO"]
    est = np.array([0.441, 0.038, 0.002, -0.264])
    ci95 = np.array([0.018, 0.029, 0.031, 0.041])
    return CoefForestInput(terms=terms, estimate=est,
                           ci_lo=est - ci95, ci_hi=est + ci95,
                           highlight=["sex_M×geno_KO"])


def partial_dependence(ax, contract, palette: str = "okabe_ito"):
    """PDP line with optional ICE-line bundle."""

    c = PartialDependenceInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 3)
    if c.ice is not None:
        ice = np.asarray(c.ice, dtype=float)
        for i in range(min(ice.shape[0], 25)):
            ax.plot(c.grid, ice[i], color=pal[1 % len(pal)], alpha=0.18, linewidth=0.5)
    ax.plot(c.grid, c.mean, color="#111", linewidth=1.6)
    ax.set_xlabel("feature value")
    ax.set_ylabel("partial dependence")
    return ax


def demo_partial_dependence() -> PartialDependenceInput:
    rng = np.random.default_rng(60)
    grid = np.linspace(-3, 3, 60)
    mean = np.tanh(grid)
    ice = np.tanh(grid + rng.normal(0, 0.4, size=(30, 1))) + rng.normal(0, 0.1, size=(30, grid.size))
    return PartialDependenceInput(grid=grid, mean=mean, ice=ice)


def random_effects_caterpillar(ax, contract, palette: str = "okabe_ito"):
    """Caterpillar plot of per-cluster deviations, sorted by estimate."""

    c = RandomEffectsInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 4)
    est = np.asarray(c.estimate); se = np.asarray(c.se)
    order = np.argsort(est)
    sorted_terms = [c.cluster[i] for i in order]
    sorted_est = est[order]; sorted_se = se[order]
    y = np.arange(len(order))
    ax.hlines(y, sorted_est - 1.96 * sorted_se, sorted_est + 1.96 * sorted_se,
              color=pal[0], linewidth=0.8)
    ax.scatter(sorted_est, y, color=pal[0], s=16, edgecolor="white", linewidth=0.4)
    ax.axvline(0.0, color="#B0BEC5", linewidth=0.5, linestyle="--")
    ax.set_yticks(y[::max(1, len(y) // 12)])
    ax.set_yticklabels([sorted_terms[i] for i in y[::max(1, len(y) // 12)]],
                       fontsize=6)
    ax.set_xlabel("estimate")
    return ax


def demo_random_effects_caterpillar() -> RandomEffectsInput:
    rng = np.random.default_rng(61)
    n = 24
    est = rng.normal(0, 0.3, size=n)
    se = np.abs(rng.normal(0, 0.08, size=n)) + 0.05
    return RandomEffectsInput(cluster=[f"A{i:02d}" for i in range(n)],
                              estimate=est, se=se)


DEMOS = {
    "coef_forest": (coef_forest, demo_coef_forest),
    "partial_dependence": (partial_dependence, demo_partial_dependence),
    "random_effects_caterpillar": (random_effects_caterpillar, demo_random_effects_caterpillar),
}
