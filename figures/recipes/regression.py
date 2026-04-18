"""Regression and diagnostic recipes.

Contains:
    scatter_with_ci        — OLS line with bootstrap-free normal CI + stats box
    bland_altman           — difference vs mean with limits of agreement
    residuals_vs_fitted    — residual diagnostic
    qq_plot                — normal Q-Q with 95 % envelope
"""
from __future__ import annotations

import numpy as np
from scipy.stats import linregress, norm, t as student_t

from ..core.contract import (
    BlandAltmanInput,
    QQInput,
    ResidualsInput,
    ScatterWithCIInput,
)
from ..core.palette import get_palette
from ..core.primitives import callout_box, dashed_reference, iter_palette


def scatter_with_ci(ax, contract, palette: str = "okabe_ito"):
    """Scatter + OLS line + 95 % CI band of the mean + stats callout."""

    c = ScatterWithCIInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 4)
    x = np.asarray(c.x, dtype=float)
    y = np.asarray(c.y, dtype=float)
    finite = np.isfinite(x) & np.isfinite(y)
    x = x[finite]; y = y[finite]
    if len(x) < 3:
        callout_box(ax, 0.5, 0.5, "<3 finite points", ha="center", va="center",
                    color="#991B1B")
        return ax
    ax.scatter(x, y, s=12, alpha=0.55, color=pal[0], edgecolor="white", linewidth=0.3)
    slope, intercept, r, p, se = linregress(x, y)
    xs = np.linspace(x.min(), x.max(), 200)
    yhat = slope * xs + intercept
    ax.plot(xs, yhat, color="#111", linewidth=1.4)
    # CI of the mean via standard linear-regression formula.
    dof = max(len(x) - 2, 1)
    tcrit = float(student_t.ppf(0.975, dof))
    mse = np.sum((y - (slope * x + intercept)) ** 2) / dof
    sxx = float(np.sum((x - x.mean()) ** 2))
    ci = tcrit * np.sqrt(mse * (1.0 / len(x) + (xs - x.mean()) ** 2 / max(sxx, 1e-12)))
    ax.fill_between(xs, yhat - ci, yhat + ci, color="#111", alpha=0.12, linewidth=0)
    ax.set_xlabel(c.xlabel)
    ax.set_ylabel(c.ylabel)
    callout_box(ax, 0.03, 0.96, f"slope={slope:.2f}\nR²={r ** 2:.2f}\np={p:.2g}",
                ha="left", va="top", color="#333333")
    return ax


def demo_scatter_with_ci() -> ScatterWithCIInput:
    rng = np.random.default_rng(3)
    x = np.linspace(0, 10, 60)
    y = 0.6 * x + 1.0 + rng.normal(0, 0.7, size=x.size)
    return ScatterWithCIInput(x=x, y=y, xlabel="predictor", ylabel="response")


def bland_altman(ax, contract, palette: str = "okabe_ito"):
    """Difference vs mean with ±1.96·SD limits of agreement."""

    c = BlandAltmanInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 3)
    a = np.asarray(c.a, dtype=float); b = np.asarray(c.b, dtype=float)
    mean = 0.5 * (a + b)
    diff = a - b
    mu = float(diff.mean())
    sd = float(diff.std(ddof=1))
    ax.scatter(mean, diff, s=14, alpha=0.6, color=pal[0],
               edgecolor="white", linewidth=0.3)
    ax.axhline(mu, color="#111", linewidth=1.0)
    for bound, label in ((mu + 1.96 * sd, "+1.96 SD"), (mu - 1.96 * sd, "−1.96 SD")):
        ax.axhline(bound, color=pal[1 % len(pal)], linewidth=0.8, linestyle="--")
    ax.set_xlabel(f"mean({c.label_a}, {c.label_b})")
    ax.set_ylabel(f"{c.label_a} − {c.label_b}")
    callout_box(ax, 0.03, 0.96, f"bias={mu:.2f}\nSD={sd:.2f}",
                ha="left", va="top", color="#333333")
    return ax


def demo_bland_altman() -> BlandAltmanInput:
    rng = np.random.default_rng(6)
    truth = rng.uniform(0, 100, size=80)
    a = truth + rng.normal(0, 3, size=80)
    b = truth + rng.normal(0, 3, size=80) + 2.0
    return BlandAltmanInput(a=a, b=b, label_a="method A", label_b="method B")


def residuals_vs_fitted(ax, contract, palette: str = "okabe_ito"):
    """Residuals vs fitted values — LOWESS-free diagnostic scatter."""

    c = ResidualsInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 4)
    ax.scatter(c.fitted, c.residuals, s=12, alpha=0.55,
               color=pal[0], edgecolor="white", linewidth=0.3)
    ax.axhline(0.0, color="#111", linewidth=0.8)
    ax.set_xlabel("fitted")
    ax.set_ylabel("residual")
    return ax


def demo_residuals_vs_fitted() -> ResidualsInput:
    rng = np.random.default_rng(13)
    fitted = np.linspace(0, 10, 120)
    residuals = rng.normal(0, 0.5 + 0.05 * fitted, size=fitted.size)
    return ResidualsInput(fitted=fitted, residuals=residuals)


def qq_plot(ax, contract, palette: str = "okabe_ito"):
    """Normal Q-Q with 95 % pointwise envelope."""

    c = QQInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 3)
    sample = np.sort(np.asarray(c.sample, dtype=float))
    n = len(sample)
    if n == 0:
        return ax
    q_theoretical = norm.ppf((np.arange(n) + 0.5) / n)
    ax.scatter(q_theoretical, sample, s=14, alpha=0.6, color=pal[0],
               edgecolor="white", linewidth=0.3)
    lo, hi = min(q_theoretical.min(), sample.min()), max(q_theoretical.max(), sample.max())
    ax.plot([lo, hi], [lo, hi], color="#111", linewidth=1.0)
    # 95 % envelope via Filliben approximation.
    mu = sample.mean(); sd = sample.std(ddof=1)
    se = sd / np.sqrt(n) * np.sqrt(1 + q_theoretical ** 2 / 2)
    ax.fill_between(q_theoretical, (mu + q_theoretical * sd) - 1.96 * se,
                    (mu + q_theoretical * sd) + 1.96 * se,
                    color=pal[1 % len(pal)], alpha=0.15, linewidth=0)
    ax.set_xlabel("theoretical quantile")
    ax.set_ylabel("sample quantile")
    return ax


def demo_qq_plot() -> QQInput:
    rng = np.random.default_rng(14)
    return QQInput(sample=rng.standard_normal(200))


DEMOS = {
    "scatter_with_ci": (scatter_with_ci, demo_scatter_with_ci),
    "bland_altman": (bland_altman, demo_bland_altman),
    "residuals_vs_fitted": (residuals_vs_fitted, demo_residuals_vs_fitted),
    "qq_plot": (qq_plot, demo_qq_plot),
}

_ = dashed_reference  # keep import used when extending with stim markers
