"""Sensitivity-analysis recipes.

Contains:
    sobol_bar                  — first-order or total-order Sobol indices
    morris_bar                 — Morris μ* with σ whisker
    ranked_contributions       — generic ranked decomposition bars
    parameter_scan_hexbin      — hexbin of output vs one swept parameter
    dimensionless_collapse     — log-log regression with CI + slope box

Every function takes ``(ax, contract, palette="okabe_ito", **opts)`` and
returns the same ``ax``. Each exposes a ``demo_<name>()`` builder for
smoke-testing.
"""
from __future__ import annotations

import numpy as np
from matplotlib import colormaps
from scipy.stats import linregress

from ..core.contract import (
    DimensionlessCollapseInput,
    MorrisInput,
    ParameterScanInput,
    RankedContributionInput,
    SobolInput,
)
from ..core.palette import get_palette
from ..core.primitives import callout_box, dashed_reference, right_of_ci_label, smart_fmt


def sobol_bar(ax, contract, palette: str = "okabe_ito", *,
              which: str = "S1", cmap: str = "viridis", order: str = "descending"):
    """Horizontal Sobol indices with CI whiskers and right-of-bar value labels.

    ``which`` selects ``"S1"`` (first-order, default) or ``"ST"`` (total-order).
    When ``which="ST"``, the contract **must** also supply ``ST`` values and
    ``ST_ci`` — the recipe refuses to fall back to ``S1_ci`` because that would
    render misleading error bars. If ``ST`` is provided without ``ST_ci``,
    the whiskers are omitted rather than reusing first-order CIs.
    """

    c = SobolInput.model_validate(contract)
    which_key = which.upper()
    if which_key == "ST":
        if c.ST is None:
            raise ValueError("sobol_bar(which='ST') requires SobolInput.ST")
        values = np.asarray(c.ST, dtype=float)
        errs = None if c.ST_ci is None else np.asarray(c.ST_ci, dtype=float)
    else:
        values = np.asarray(c.S1, dtype=float)
        errs = np.asarray(c.S1_ci, dtype=float)

    ascending = order.lower() != "descending"
    idx = np.argsort(values)
    if not ascending:
        idx = idx[::-1]
    params = [c.parameters[i] for i in idx]
    vals = values[idx]
    sorted_errs = errs[idx] if errs is not None else None
    cm = colormaps.get_cmap(cmap)
    colors = cm(np.linspace(0.18, 0.85, len(vals)))
    ax.barh(params, vals, xerr=sorted_errs, color=colors, edgecolor="#222",
            linewidth=0.5, error_kw=dict(ecolor="#333", lw=0.7, capsize=2))
    # Label placement: right of the upper CI if we have one, otherwise right of the bar.
    label_offsets = vals + (sorted_errs if sorted_errs is not None else np.zeros_like(vals))
    for i, (v, upper) in enumerate(zip(vals, label_offsets)):
        right_of_ci_label(ax, upper=upper, y=i, text=smart_fmt(v), color="#222")
    ax.set_xlim(0, float(vals.max()) * 1.30 if len(vals) else 1.0)
    ax.set_xlabel(f"Sobol {which_key}")
    get_palette(palette)  # validate palette exists
    return ax


def demo_sobol_bar() -> SobolInput:
    return SobolInput(
        parameters=["v_poly", "k_cap", "E_bundle", "L_0", "Pi_3"],
        S1=np.array([0.58, 0.22, 0.09, 0.05, 0.03]),
        S1_ci=np.array([0.045, 0.038, 0.020, 0.015, 0.010]),
        ST=np.array([0.71, 0.38, 0.19, 0.17, 0.11]),
        ST_ci=np.array([0.055, 0.049, 0.031, 0.028, 0.021]),
        n_samples=1024,
    )


def morris_bar(ax, contract, palette: str = "okabe_ito"):
    """Morris μ* (bars) with σ (thin whiskers) — ranked by μ*."""

    c = MorrisInput.model_validate(contract)
    order = np.argsort(c.mu_star)[::-1]
    params = [c.parameters[i] for i in order]
    mus = np.asarray(c.mu_star)[order]
    sig = np.asarray(c.sigma)[order]
    pal = get_palette(palette).categorical
    ax.barh(params, mus, color=pal[0], edgecolor="#222", linewidth=0.5)
    ax.errorbar(mus, np.arange(len(mus)), xerr=sig, fmt="none",
                ecolor="#333", lw=0.7, capsize=2)
    ax.set_xlabel("Morris μ*")
    return ax


def demo_morris_bar() -> MorrisInput:
    return MorrisInput(
        parameters=["R_src", "k_H", "a_L", "k_S", "d_S", "R_surv"],
        mu_star=np.array([2.0, 0.9, 0.8, 0.4, 0.3, 0.2]),
        sigma=np.array([0.7, 0.35, 0.30, 0.18, 0.12, 0.10]),
    )


def ranked_contributions(ax, contract, palette: str = "okabe_ito"):
    """Generic ranked bar for any decomposition (variance, importance, SHAP)."""

    c = RankedContributionInput.model_validate(contract)
    order = np.argsort(c.values)[::-1]
    labels = [c.labels[i] for i in order]
    vals = np.asarray(c.values)[order]
    errs = np.asarray(c.error)[order] if c.error is not None else np.zeros_like(vals)
    pal = get_palette(palette).categorical
    ax.barh(labels, vals, xerr=errs, color=pal[1 % len(pal)],
            edgecolor="#222", linewidth=0.5,
            error_kw=dict(ecolor="#333", lw=0.7, capsize=2))
    for i, (v, e) in enumerate(zip(vals, errs)):
        right_of_ci_label(ax, upper=v + e, y=i, text=smart_fmt(v))
    ax.set_xlim(0, float(vals.max()) * 1.30 if len(vals) else 1.0)
    return ax


def demo_ranked_contributions() -> RankedContributionInput:
    return RankedContributionInput(
        labels=["contractility", "polymerization", "adhesion", "membrane", "signaling"],
        values=np.array([0.42, 0.30, 0.15, 0.08, 0.05]),
        error=np.array([0.03, 0.03, 0.02, 0.015, 0.010]),
    )


def parameter_scan_hexbin(ax, contract, palette: str = "okabe_ito"):
    """Hexbin of a paired parameter scan with an optional reference line + box."""

    c = ParameterScanInput.model_validate(contract)
    pal = get_palette(palette)
    hb = ax.hexbin(c.x, c.y, gridsize=int(c.gridsize), cmap=pal.density, mincnt=1)
    ax.figure.colorbar(hb, ax=ax, shrink=0.85, pad=0.02, label="count")
    if c.reference is not None:
        dashed_reference(ax, c.reference, axis="x", color="#1B5E20", label=None)
    if c.annotation:
        callout_box(ax, 0.02, 0.96, c.annotation, ha="left", va="top",
                    color="#333333")
    return ax


def demo_parameter_scan_hexbin() -> ParameterScanInput:
    rng = np.random.default_rng(3)
    x = rng.uniform(0.05, 0.6, size=300)
    y = 35.0 * np.sqrt(x) + rng.normal(0, 2.2, size=300)
    return ParameterScanInput(x=x, y=y, gridsize=18, reference=0.35,
                              annotation="N=300 samples")


def dimensionless_collapse(ax, contract, palette: str = "okabe_ito"):
    """Log-log regression with scatter, OLS line, and a slope/R² callout."""

    c = DimensionlessCollapseInput.model_validate(contract)
    pal = get_palette(palette).categorical
    ax.scatter(c.log_x, c.log_y, s=12, alpha=0.55, color=pal[4 % len(pal)],
               edgecolor="white", linewidth=0.3)
    slope, intercept, r, p, se = linregress(c.log_x, c.log_y)
    xs = np.linspace(c.log_x.min(), c.log_x.max(), 120)
    ax.plot(xs, slope * xs + intercept, color="#111", linewidth=1.4)
    ax.set_xlabel(c.x_label)
    ax.set_ylabel(c.y_label)
    callout_box(ax, 0.03, 0.96,
                f"slope={slope:.2f}\nR²={r**2:.2f}", ha="left", va="top",
                color="#333333")
    return ax


def demo_dimensionless_collapse() -> DimensionlessCollapseInput:
    rng = np.random.default_rng(7)
    log_x = np.linspace(-2.0, 2.0, 120)
    log_y = 0.92 * log_x + 0.2 + rng.normal(0, 0.25, size=120)
    return DimensionlessCollapseInput(log_x=log_x, log_y=log_y,
                                      x_label="log Π₃", y_label="log L_max")


DEMOS = {
    "sobol_bar": (sobol_bar, demo_sobol_bar),
    "morris_bar": (morris_bar, demo_morris_bar),
    "ranked_contributions": (ranked_contributions, demo_ranked_contributions),
    "parameter_scan_hexbin": (parameter_scan_hexbin, demo_parameter_scan_hexbin),
    "dimensionless_collapse": (dimensionless_collapse, demo_dimensionless_collapse),
}
