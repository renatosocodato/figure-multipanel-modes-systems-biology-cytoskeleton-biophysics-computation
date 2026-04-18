"""Dynamical-systems recipes.

Contains:
    phase_portrait           — contour backdrop + streamplot + fixed points
    potential_1d             — U(x) for multiple conditions
    bifurcation              — stable / unstable branches with saddle-node
    nullclines               — paired dx=0 / dy=0 curves + intersections
    limit_cycle_portrait     — trajectory + Poincaré section

The RHS/potential callables come through the :class:`DynamicsInput`
contract so callers decouple computation from visualization.
"""
from __future__ import annotations

import numpy as np

from ..core.contract import BifurcationInput, DynamicsInput, LimitCycleInput
from ..core.palette import get_palette
from ..core.primitives import (
    callout_box,
    dashed_reference,
    halo_text,
    iter_palette,
    saddle_marker,
    stable_fixed_point,
)


def _supports_cond(fn) -> bool:
    try:
        from inspect import signature
        return "cond" in signature(fn).parameters
    except (ValueError, TypeError):
        return False


def phase_portrait(ax, contract, palette: str = "home_gate_trap", *,
                   condition: str = "basal", nullclines: bool = False):
    """Contour backdrop + streamplot + fixed-point overlay."""

    c = DynamicsInput.model_validate(contract)
    pal = get_palette(palette)
    # Contour backdrop from U(x) projected via 2D extension.
    if c.U is not None:
        xg = np.linspace(c.xlim[0] + 1e-3, c.xlim[1], 200)
        yg = np.linspace(c.ylim[0] + 1e-3, c.ylim[1], 200)
        XX, YY = np.meshgrid(xg, yg)
        UU = c.U(XX, condition) + 0.5 * 0.45 * (XX - YY) ** 2
        lo, hi = np.percentile(UU, 3), np.percentile(UU, 85)
        ax.contourf(XX, YY, np.clip(UU, lo, hi), levels=20, cmap="Blues_r",
                    alpha=0.35, zorder=0)
        ax.contour(XX, YY, UU, levels=np.linspace(lo, hi, 8),
                   colors="#7A8AA3", linewidths=0.45, alpha=0.55, zorder=1)
    # Vector field via provided RHS.
    if c.rhs_2D is not None:
        xx, yy = np.meshgrid(
            np.linspace(c.xlim[0] + 0.05, c.xlim[1] - 0.05, c.grid),
            np.linspace(c.ylim[0] + 0.05, c.ylim[1] - 0.05, c.grid),
        )
        U_grid = np.zeros_like(xx); V_grid = np.zeros_like(yy)
        for i in range(c.grid):
            for j in range(c.grid):
                state = [xx[i, j], yy[i, j]]
                if _supports_cond(c.rhs_2D):
                    dx, dy = c.rhs_2D(state, condition)
                else:
                    dx, dy = c.rhs_2D(state)
                U_grid[i, j], V_grid[i, j] = dx, dy
        speed = np.sqrt(U_grid ** 2 + V_grid ** 2)
        ax.streamplot(xx, yy, U_grid, V_grid, color=np.log1p(speed),
                      cmap=pal.continuous, density=1.15, linewidth=0.6, arrowsize=0.75,
                      zorder=2)
    if nullclines:
        ax.plot(c.xlim, c.ylim, color="#009E73", linewidth=1.2, linestyle="--",
                alpha=0.9, zorder=3)
    if c.fixed_points:
        for xv, yv, kind, name in c.fixed_points:
            col = pal.semantic.get(name.lower().split("_")[0], "#111111")
            if kind == "stable":
                stable_fixed_point(ax, xv, yv, color=col, name=name.upper())
            else:
                saddle_marker(ax, xv, yv)
    ax.set_xlim(c.xlim); ax.set_ylim(c.ylim)
    return ax


def _demo_U(x, cond: str = "basal"):
    centers = np.array([0.15, 0.95, 2.25])
    widths = np.array([0.20, 0.28, 0.32])
    weights = np.array([2.5, 2.6, 2.8])
    if cond == "rocki":
        weights = weights * np.array([0.88, 1.3, 1.0])
    elif cond == "srci":
        weights = weights * np.array([1.0, 1.0, 0.62])
    x = np.asarray(x, dtype=float)
    return 0.1 * x ** 2 - sum(
        weights[i] * np.exp(-((x - centers[i]) / widths[i]) ** 2) for i in range(3)
    )


def _demo_rhs(state, cond: str = "basal", k_y: float = 0.8):
    x, y = state
    centers = np.array([0.15, 0.95, 2.25])
    widths = np.array([0.20, 0.28, 0.32])
    weights = np.array([2.5, 2.6, 2.8])
    if cond == "rocki":
        weights = weights * np.array([0.88, 1.3, 1.0])
    elif cond == "srci":
        weights = weights * np.array([1.0, 1.0, 0.62])
    dU_dx = 2 * 0.1 * x
    for i in range(3):
        s = widths[i]
        dU_dx += (weights[i] * 2 * (x - centers[i]) / s ** 2
                  * np.exp(-((x - centers[i]) / s) ** 2))
    return [float(-dU_dx), float(k_y * (x - y))]


def demo_phase_portrait() -> DynamicsInput:
    fixed_points = [
        (0.15, 0.15, "stable", "home"),
        (0.5, 0.5, "saddle", "saddle_hg"),
        (0.95, 0.95, "stable", "gate"),
        (1.6, 1.6, "saddle", "saddle_gt"),
        (2.25, 2.25, "stable", "trap"),
    ]
    return DynamicsInput(
        U=_demo_U, rhs_2D=_demo_rhs, conditions=["basal"],
        xlim=(0.0, 3.0), ylim=(0.0, 3.0), grid=14, fixed_points=fixed_points,
    )


def potential_1d(ax, contract, palette: str = "home_gate_trap"):
    """Overlay U(x) for each condition in the contract."""

    c = DynamicsInput.model_validate(contract)
    if c.U is None:
        raise ValueError("potential_1d requires DynamicsInput.U")
    pal = iter_palette(get_palette(palette).categorical, 6)
    x = np.linspace(c.xlim[0], c.xlim[1], 400)
    for i, cond in enumerate(c.conditions):
        ax.plot(x, c.U(x, cond), color=pal[i % len(pal)], linewidth=1.6, label=cond)
    if c.fixed_points:
        for xv, _, kind, name in c.fixed_points:
            if kind == "stable":
                dashed_reference(ax, xv, axis="x", color="#B0BEC5", label=name.upper())
    ax.set_xlabel("x"); ax.set_ylabel("U(x)")
    ax.legend(fontsize=7.5, frameon=False)
    return ax


def demo_potential_1d() -> DynamicsInput:
    c = demo_phase_portrait()
    return DynamicsInput(U=c.U, rhs_2D=c.rhs_2D, conditions=["basal", "rocki", "srci"],
                         xlim=c.xlim, ylim=c.ylim, grid=c.grid, fixed_points=c.fixed_points)


def bifurcation(ax, contract, palette: str = "home_gate_trap"):
    """Stable (solid) / unstable (dashed) branches with optional saddle-node star."""

    c = BifurcationInput.model_validate(contract)
    pal = get_palette(palette)
    style_of = {
        "home": ("-", pal.semantic.get("home", "#1B5E20")),
        "gate": ("-", pal.semantic.get("gate", "#F9A825")),
        "trap": ("-", pal.semantic.get("trap", "#C62828")),
    }
    for name, arr in c.branches.items():
        arr = np.asarray(arr, dtype=float)
        if "saddle" in name.lower() or "unstable" in name.lower():
            ls = "--"; color = "#455A64"
        else:
            ls, color = style_of.get(name.lower(), ("-", "#111111"))
        ax.plot(c.r, arr, linestyle=ls, color=color, linewidth=1.4, label=name)
    if c.saddle_node is not None and c.saddle_node_branch is not None:
        branch_name = c.saddle_node_branch
        if branch_name not in c.branches:
            raise KeyError(
                f"saddle_node_branch={branch_name!r} not present in branches: "
                f"{sorted(c.branches)}"
            )
        branch_arr = np.asarray(c.branches[branch_name], dtype=float)
        finite = np.isfinite(branch_arr)
        if finite.any():
            sn_y = float(np.interp(c.saddle_node, c.r[finite], branch_arr[finite]))
            ax.scatter([c.saddle_node], [sn_y], marker="*", s=80, color="#111",
                       zorder=6)
    ax.set_xlabel("bifurcation parameter")
    ax.set_ylabel("state")
    ax.legend(fontsize=7.5, frameon=False)
    return ax


def demo_bifurcation() -> BifurcationInput:
    r = np.linspace(0.0, 1.0, 120)
    frac = np.clip(r / 0.45, 0.0, 1.0)
    home = np.where(r < 0.45, 0.15 + 0.17 * frac ** 2, np.nan)
    hgs = np.where(r < 0.45, 0.50 - 0.18 * frac ** 2, np.nan)
    gate = 0.95 + 0.08 * r
    trap = np.full_like(r, 2.25)
    return BifurcationInput(r=r, branches={"home": home, "hgs": hgs,
                                           "gate": gate, "trap": trap},
                            saddle_node=0.45, saddle_node_branch="home")


def nullclines(ax, contract, palette: str = "okabe_ito"):
    """Dummy nullcline pair — computed analytically from the contract's RHS."""

    c = DynamicsInput.model_validate(contract)
    if c.rhs_2D is None:
        raise ValueError("nullclines requires DynamicsInput.rhs_2D")
    pal = iter_palette(get_palette(palette).categorical, 3)
    xs = np.linspace(c.xlim[0] + 1e-3, c.xlim[1], 200)
    ys = np.linspace(c.ylim[0] + 1e-3, c.ylim[1], 200)
    XX, YY = np.meshgrid(xs, ys)
    dX = np.zeros_like(XX); dY = np.zeros_like(YY)
    for i in range(XX.shape[0]):
        for j in range(XX.shape[1]):
            state = [XX[i, j], YY[i, j]]
            dx, dy = (c.rhs_2D(state, c.conditions[0]) if _supports_cond(c.rhs_2D)
                      else c.rhs_2D(state))
            dX[i, j], dY[i, j] = dx, dy
    ax.contour(XX, YY, dX, levels=[0.0], colors=pal[0], linewidths=1.2)
    ax.contour(XX, YY, dY, levels=[0.0], colors=pal[1 % len(pal)], linewidths=1.2)
    if c.fixed_points:
        for xv, yv, kind, _ in c.fixed_points:
            (stable_fixed_point if kind == "stable" else saddle_marker)(ax, xv, yv)
    ax.set_xlim(c.xlim); ax.set_ylim(c.ylim)
    halo_text(ax, c.xlim[0] + 0.1 * (c.xlim[1] - c.xlim[0]),
              c.ylim[1] - 0.08 * (c.ylim[1] - c.ylim[0]),
              "dx=0 / dy=0", color="#333", fontsize=8, ha="left", va="top")
    return ax


def demo_nullclines() -> DynamicsInput:
    return demo_phase_portrait()


def limit_cycle_portrait(ax, contract, palette: str = "okabe_ito"):
    """Closed-orbit trajectory with an optional Poincaré section line."""

    c = LimitCycleInput.model_validate(contract)
    pal = iter_palette(get_palette(palette).categorical, 3)
    xy = np.asarray(c.xy)
    ax.plot(xy[:, 0], xy[:, 1], color=pal[0], linewidth=1.2)
    if c.poincare_x is not None:
        ax.axvline(c.poincare_x, color=pal[1 % len(pal)], linestyle="--", linewidth=0.9)
        callout_box(ax, 0.02, 0.96, f"Poincaré @ x={c.poincare_x:.2g}",
                    ha="left", va="top", color="#333333")
    ax.set_xlabel("x"); ax.set_ylabel("y")
    return ax


def demo_limit_cycle_portrait() -> LimitCycleInput:
    t = np.linspace(0, 2 * np.pi, 400)
    xy = np.column_stack([np.cos(t), np.sin(t) + 0.15 * np.sin(3 * t)])
    return LimitCycleInput(t=t, xy=xy, poincare_x=0.0)


DEMOS = {
    "phase_portrait": (phase_portrait, demo_phase_portrait),
    "potential_1d": (potential_1d, demo_potential_1d),
    "bifurcation": (bifurcation, demo_bifurcation),
    "nullclines": (nullclines, demo_nullclines),
    "limit_cycle_portrait": (limit_cycle_portrait, demo_limit_cycle_portrait),
}
