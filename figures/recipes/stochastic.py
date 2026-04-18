"""Stochastic / Gillespie recipes.

Contains:
    dwell_violin            — per-state dwell-time violins with median bars
    gillespie_trajectories  — overlaid stochastic trajectories
    fpt_ecdf                — first-passage-time ECDF with Weibull fit
    rate_vs_parameter       — transition rate log-log with optional SEM
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, weibull_min

from ..core.contract import DwellInput, FPTInput, GillespieInput, RateScanInput
from ..core.palette import get_palette
from ..core.primitives import callout_box, iter_palette


def dwell_violin(ax, contract, palette: str = "home_gate_trap"):
    """Per-state dwell-time violins with median + IQR overlay."""

    c = DwellInput.model_validate(contract)
    pal = get_palette(palette)
    states = list(c.df[c.state_col].dropna().unique())
    for i, state in enumerate(states):
        vals = c.df.loc[c.df[c.state_col] == state, c.log10_dwell_col].dropna().values
        if len(vals) == 0:
            continue
        col = pal.semantic.get(state.lower(), pal.categorical[i % len(pal.categorical)])
        median = float(np.median(vals))
        # Degenerate cohorts (constant values) make gaussian_kde singular; draw
        # a tick at the shared value instead so the state still appears.
        if len(vals) < 3 or float(np.ptp(vals)) <= 0.0 or float(np.var(vals)) <= 1e-18:
            ax.hlines(median, i - 0.25, i + 0.25, color=col, linewidth=1.2)
            continue
        kde = gaussian_kde(vals)
        ys = np.linspace(vals.min(), vals.max(), 128)
        xs = kde(ys); xs = xs / xs.max() * 0.38
        ax.fill_betweenx(ys, i - xs, i + xs, color=col, alpha=0.75, linewidth=0.5,
                         edgecolor="#222")
        q1, q3 = np.percentile(vals, [25, 75])
        ax.hlines([median], i - 0.25, i + 0.25, color="#111", linewidth=1.2)
        ax.vlines(i, q1, q3, color="#111", linewidth=0.8)
    ax.set_xticks(range(len(states)))
    ax.set_xticklabels([str(s) for s in states])
    ax.set_ylabel(c.log10_dwell_col)
    return ax


def demo_dwell_violin() -> DwellInput:
    rng = np.random.default_rng(30)
    rows = []
    for state, center in (("HOME", 3.0), ("GATE", 1.4), ("TRAP", 4.1)):
        rows.extend([{"state": state, "log10_dwell_s": v}
                     for v in rng.normal(center, 0.15, size=80)])
    return DwellInput(df=pd.DataFrame(rows))


def gillespie_trajectories(ax, contract, palette: str = "okabe_ito"):
    """Overlay a small number of Gillespie step traces."""

    c = GillespieInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 6)
    traj = np.asarray(c.trajectories, dtype=float)
    t = np.asarray(c.t, dtype=float)
    for k in range(min(traj.shape[0], 8)):
        ax.step(t, traj[k], where="post", color=pal[k % len(pal)], linewidth=0.7,
                alpha=0.9)
    ax.set_xlabel("time"); ax.set_ylabel("count")
    return ax


def demo_gillespie_trajectories() -> GillespieInput:
    rng = np.random.default_rng(22)
    t = np.linspace(0, 40, 200)
    traj = np.zeros((6, t.size))
    for i in range(6):
        steps = rng.choice([-1, 1], size=t.size, p=[0.45, 0.55])
        traj[i] = np.cumsum(steps) + 30 + i * 1.5
    return GillespieInput(t=t, trajectories=traj)


def fpt_ecdf(ax, contract, palette: str = "okabe_ito"):
    """Empirical CDF of first-passage times + a Weibull fit overlay."""

    c = FPTInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 3)
    samples = np.sort(np.asarray(c.samples, dtype=float))
    n = len(samples)
    if n == 0:
        return ax
    ys = np.arange(1, n + 1) / n
    ax.step(samples, ys, where="post", color=pal[0], linewidth=1.4, label="empirical")
    try:
        shape_, loc_, scale_ = weibull_min.fit(samples, floc=0.0)
        grid = np.linspace(samples.min(), samples.max(), 200)
        ax.plot(grid, weibull_min.cdf(grid, shape_, loc_, scale_),
                color="#111", linewidth=1.0, linestyle="--", label="Weibull fit")
        callout_box(ax, 0.03, 0.96, f"k={shape_:.2f}\nλ={scale_:.2f}",
                    ha="left", va="top", color="#333333")
    except (RuntimeError, ValueError):
        pass
    ax.set_xlabel("first-passage time")
    ax.set_ylabel("F(t)")
    ax.legend(fontsize=7.5, frameon=False)
    return ax


def demo_fpt_ecdf() -> FPTInput:
    rng = np.random.default_rng(10)
    return FPTInput(samples=rng.weibull(1.4, size=200) * 3.0)


def rate_vs_parameter(ax, contract, palette: str = "okabe_ito"):
    """Log-log plot of a transition rate vs a swept parameter."""

    c = RateScanInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 3)
    x = np.asarray(c.parameter, dtype=float)
    y = np.asarray(c.rate, dtype=float)
    ax.plot(x, y, "o-", color=pal[0], linewidth=1.2, markersize=4)
    if c.sem is not None:
        sem = np.asarray(c.sem, dtype=float)
        ax.fill_between(x, y - sem, y + sem, color=pal[0], alpha=0.2, linewidth=0)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(c.parameter_label); ax.set_ylabel(c.rate_label)
    return ax


def demo_rate_vs_parameter() -> RateScanInput:
    x = np.logspace(-2, 1, 20)
    y = 1.5 * x ** 1.2
    return RateScanInput(parameter=x, rate=y, sem=0.08 * y,
                         parameter_label="ROCK inhibition", rate_label="k_escape (s⁻¹)")


DEMOS = {
    "dwell_violin": (dwell_violin, demo_dwell_violin),
    "gillespie_trajectories": (gillespie_trajectories, demo_gillespie_trajectories),
    "fpt_ecdf": (fpt_ecdf, demo_fpt_ecdf),
    "rate_vs_parameter": (rate_vs_parameter, demo_rate_vs_parameter),
}
