"""Timecourse recipes.

Contains:
    hierarchical_ci_line     — cluster-level 95 % CI band
    dose_response            — Hill fit with CI and EC50 annotation
    fret_traces              — per-cell traces with ensemble mean overlay
    calcium_raster           — event raster with population rate underneath
    trajectory_bundle        — ensemble of stochastic trajectories with tube
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import norm

from ..core.contract import (
    CalciumRasterInput,
    DoseResponseInput,
    TimecourseInput,
    TrajectoryBundleInput,
)
from ..core.palette import get_palette
from ..core.primitives import callout_box, dashed_reference, iter_palette


def hierarchical_ci_line(ax, contract, palette: str = "okabe_ito"):
    """Time series with a cluster-level 95 % CI band per group.

    The CI uses the observed cluster count at each time bin, not the total
    column width, so partial cluster coverage does not shrink the band.
    """

    c = TimecourseInput.model_validate(contract)
    if c.group_col is None or c.cluster_col is None:
        raise ValueError("hierarchical_ci_line needs group_col and cluster_col")
    pal = iter_palette(get_palette(palette).categorical, 12)
    for i, (g, sub) in enumerate(c.df.groupby(c.group_col)):
        clusters = (sub.groupby([c.cluster_col, c.time_col])[c.value_col]
                    .mean().unstack(c.cluster_col))
        t = clusters.index.to_numpy()
        mean = clusters.mean(axis=1).to_numpy()
        counts = clusters.count(axis=1).to_numpy()
        std = clusters.std(axis=1, ddof=1).to_numpy()
        with np.errstate(divide="ignore", invalid="ignore"):
            sem = np.where(counts >= 2, std / np.sqrt(counts), np.nan)
        col = pal[i % len(pal)]
        ax.fill_between(t, mean - 1.96 * sem, mean + 1.96 * sem, color=col,
                        alpha=0.20, linewidth=0)
        ax.plot(t, mean, color=col, linewidth=1.8, label=str(g))
    if c.stim_time is not None:
        dashed_reference(ax, c.stim_time, axis="x", color="#455A64", label="stim")
    ax.set_xlabel(c.time_col)
    ax.set_ylabel(c.value_col)
    ax.legend(fontsize=7.5, frameon=False)
    return ax


def demo_hierarchical_ci_line() -> TimecourseInput:
    import pandas as pd
    rng = np.random.default_rng(2)
    rows = []
    for group, shift in (("ctrl", 0.0), ("drug", 0.4)):
        for animal in range(4):
            base = 0.5 + 0.2 * rng.standard_normal()
            for t in range(12):
                signal = base + shift * (t / 11.0) + rng.normal(0, 0.08)
                rows.append({"t": t, "y": signal, "grp": group, "anim": f"{group}_{animal}"})
    return TimecourseInput(df=pd.DataFrame(rows), time_col="t", value_col="y",
                           group_col="grp", cluster_col="anim", stim_time=3.0)


def _hill(x, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)


def dose_response(ax, contract, palette: str = "okabe_ito"):
    """4-parameter Hill fit, zero-dose-control safe.

    Doses ≤ 0 (typical for vehicle / zero-dose controls) are kept on the
    axis but excluded from the Hill fit. The x-axis switches to ``symlog``
    with a narrow linear window around zero whenever such values are
    present, so the control point shows up alongside the log-spaced dose
    series without forcing a divide-by-zero.
    """

    c = DoseResponseInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 2)
    dose = np.asarray(c.dose, dtype=float)
    response = np.asarray(c.response, dtype=float)
    sem = np.asarray(c.response_sem, dtype=float) if c.response_sem is not None else None

    positive = dose > 0
    has_zero = not positive.all()

    ax.errorbar(dose, response,
                yerr=sem if sem is not None else None,
                fmt="o", color=pal[0], markersize=4, capsize=2, linewidth=0.7)

    fit_dose = dose[positive]
    fit_response = response[positive]
    if len(fit_dose) >= 4:
        try:
            p0 = [float(fit_response.min()), float(fit_response.max()),
                  float(c.ec50_guess), 1.0]
            popt, _ = curve_fit(_hill, fit_dose, fit_response, p0=p0, maxfev=4000)
            xs = np.logspace(np.log10(max(fit_dose.min(), 1e-6)),
                             np.log10(fit_dose.max()), 200)
            ax.plot(xs, _hill(xs, *popt), color="#111", linewidth=1.3)
            ec50 = popt[2]
            if ec50 > 0:
                dashed_reference(ax, ec50, axis="x", color=pal[1],
                                 label=f"EC50={ec50:.2g}")
        except (RuntimeError, ValueError):
            pass

    if has_zero and positive.any():
        # Linear window wide enough for zero to render, transitioning to log.
        linthresh = float(fit_dose.min()) / 2.0
        ax.set_xscale("symlog", linthresh=max(linthresh, 1e-12))
    elif positive.any():
        ax.set_xscale("log")
    # else: all doses non-positive — leave linear so the controls still render.
    ax.set_xlabel("dose")
    ax.set_ylabel("response")
    return ax


def demo_dose_response() -> DoseResponseInput:
    dose = np.logspace(-3, 2, 14)
    response = _hill(dose, 0.1, 1.0, 0.8, 1.2)
    rng = np.random.default_rng(8)
    response = response + rng.normal(0, 0.04, size=dose.size)
    return DoseResponseInput(dose=dose, response=response,
                             response_sem=np.full_like(dose, 0.04),
                             ec50_guess=0.5)


def fret_traces(ax, contract, palette: str = "fret_donor_acceptor"):
    """Per-cell traces (group_col optional) with mean overlay."""

    c = TimecourseInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 4)
    df = c.df
    if c.group_col:
        groups = list(df[c.group_col].dropna().unique())
        for i, g in enumerate(groups):
            sub = df[df[c.group_col] == g]
            for _, trace in sub.groupby(c.cluster_col or sub.index):
                ax.plot(trace[c.time_col], trace[c.value_col], color=pal[i % len(pal)],
                        linewidth=0.5, alpha=0.3)
            mean = sub.groupby(c.time_col)[c.value_col].mean()
            ax.plot(mean.index, mean.values, color=pal[i % len(pal)], linewidth=1.8,
                    label=str(g))
        ax.legend(fontsize=7.5, frameon=False)
    else:
        for _, trace in df.groupby(c.cluster_col or df.index):
            ax.plot(trace[c.time_col], trace[c.value_col], color=pal[0],
                    linewidth=0.5, alpha=0.3)
        mean = df.groupby(c.time_col)[c.value_col].mean()
        ax.plot(mean.index, mean.values, color="#111", linewidth=1.8)
    if c.stim_time is not None:
        dashed_reference(ax, c.stim_time, axis="x", color="#455A64", label="stim")
    ax.set_xlabel(c.time_col)
    ax.set_ylabel(c.value_col)
    return ax


def demo_fret_traces() -> TimecourseInput:
    import pandas as pd
    rng = np.random.default_rng(17)
    rows = []
    for cell in range(8):
        base = rng.normal(1.0, 0.05)
        for t in np.linspace(0, 60, 30):
            signal = base + 0.25 / (1 + np.exp(-(t - 20) / 4)) + rng.normal(0, 0.03)
            rows.append({"t": t, "r": signal, "cell": cell})
    return TimecourseInput(df=pd.DataFrame(rows), time_col="t", value_col="r",
                           cluster_col="cell", stim_time=20.0)


def calcium_raster(ax, contract, palette: str = "okabe_ito"):
    """Raster plot (cell rows, time columns) + population rate overlay.

    Accepts an empty ``events`` table gracefully: the axes is annotated with
    a ``"no events"`` placeholder and no histogram is computed, so upstream
    filters that remove every event from a condition do not crash figure
    generation.
    """

    c = CalciumRasterInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 4)
    events = c.events
    ax.set_xlabel(c.time_col)
    ax.set_ylabel("cell")
    if events is None or len(events) == 0:
        ax.text(0.5, 0.5, "no events",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=8, color="#6B7280", style="italic")
        return ax
    cells = list(events[c.cell_col].drop_duplicates().sort_values())
    y_of = {cell: idx for idx, cell in enumerate(cells)}
    ax.scatter(events[c.time_col], events[c.cell_col].map(y_of),
               marker="|", color=pal[0], s=12, linewidths=0.7)
    t_min = float(events[c.time_col].min())
    t_max = float(events[c.time_col].max())
    # np.arange with start == stop yields a single edge; np.histogram needs ≥ 2.
    # When all timestamps coincide, widen the window by one bin so we get an
    # unambiguous [t_min, t_min + bin_size] histogram bin.
    if t_max <= t_min:
        t_max = t_min + float(c.bin_size)
    bins = np.arange(t_min, t_max + c.bin_size, c.bin_size)
    if bins.size < 2:
        bins = np.array([t_min, t_min + float(c.bin_size)])
    rate, edges = np.histogram(events[c.time_col].values, bins=bins)
    centers = 0.5 * (edges[:-1] + edges[1:])
    # Population rate on twin y on lower 20 %.
    ax2 = ax.twinx()
    ax2.fill_between(centers, 0, rate / max(rate.max(), 1), color=pal[1 % len(pal)],
                     alpha=0.35, linewidth=0)
    ax2.set_ylabel("rate (norm.)", color=pal[1 % len(pal)])
    ax2.spines["top"].set_visible(False)
    return ax


def demo_calcium_raster() -> CalciumRasterInput:
    import pandas as pd
    rng = np.random.default_rng(15)
    rows = []
    for cell in range(12):
        for _ in range(rng.integers(6, 20)):
            rows.append({"cell_id": cell, "t": float(rng.uniform(0, 30))})
    return CalciumRasterInput(events=pd.DataFrame(rows), bin_size=1.0)


def trajectory_bundle(ax, contract, palette: str = "okabe_ito"):
    """Stochastic trajectory ensemble with 5/50/95 percentile tube + mean."""

    c = TrajectoryBundleInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 2)
    traj = np.asarray(c.trajectories, dtype=float)
    t = np.asarray(c.t, dtype=float)
    lo = np.percentile(traj, 5, axis=0)
    hi = np.percentile(traj, 95, axis=0)
    md = np.percentile(traj, 50, axis=0)
    for k in range(min(traj.shape[0], 20)):
        ax.plot(t, traj[k], color=pal[0], alpha=0.12, linewidth=0.5)
    ax.fill_between(t, lo, hi, color=pal[0], alpha=0.25, linewidth=0)
    ax.plot(t, md, color="#111", linewidth=1.5)
    ax.set_xlabel("time")
    ax.set_ylabel("state")
    return ax


def demo_trajectory_bundle() -> TrajectoryBundleInput:
    rng = np.random.default_rng(9)
    t = np.linspace(0, 20, 200)
    traj = np.cumsum(rng.normal(0, 0.05, size=(40, t.size)), axis=1) + 0.8
    return TrajectoryBundleInput(t=t, trajectories=traj)


DEMOS = {
    "hierarchical_ci_line": (hierarchical_ci_line, demo_hierarchical_ci_line),
    "dose_response": (dose_response, demo_dose_response),
    "fret_traces": (fret_traces, demo_fret_traces),
    "calcium_raster": (calcium_raster, demo_calcium_raster),
    "trajectory_bundle": (trajectory_bundle, demo_trajectory_bundle),
}

# scipy.stats.norm stub kept for future hypothesis overlays
_ = norm, Tuple
