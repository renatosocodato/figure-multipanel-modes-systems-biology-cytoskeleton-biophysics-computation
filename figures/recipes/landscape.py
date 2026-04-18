"""Landscape / potential recipes.

Contains:
    potential_2d_heatmap       — U_2D heatmap + contours + (optional) vector field
    waddington_projection      — projected landscape with optional trajectories
"""
from __future__ import annotations

import numpy as np

from ..core.contract import Potential2DInput, WaddingtonInput
from ..core.palette import get_palette
from ..core.primitives import iter_palette, saddle_marker, stable_fixed_point


def potential_2d_heatmap(ax, contract, palette: str = "home_gate_trap"):
    """U_2D as a heatmap with isocontours + (optional) streamlines."""

    c = Potential2DInput.model_validate(contract)
    X, Y, U = np.asarray(c.X), np.asarray(c.Y), np.asarray(c.U)
    pal = get_palette(palette)
    hm = ax.pcolormesh(X, Y, U, cmap=pal.density, shading="auto")
    ax.figure.colorbar(hm, ax=ax, shrink=0.85, pad=0.02, label="U(x,y)")
    lo, hi = np.percentile(U, 5), np.percentile(U, 95)
    ax.contour(X, Y, U, levels=np.linspace(lo, hi, 9),
               colors="white", linewidths=0.4, alpha=0.55)
    if c.vector_field is not None:
        U_grid, V_grid = [np.asarray(a) for a in c.vector_field]
        step = max(1, U_grid.shape[0] // 18)
        ax.quiver(X[::step, ::step], Y[::step, ::step],
                  U_grid[::step, ::step], V_grid[::step, ::step],
                  color="white", width=0.002, alpha=0.65)
    if c.fixed_points:
        for xv, yv, kind, name in c.fixed_points:
            col = pal.semantic.get(name.lower().split("_")[0], "#111111")
            if kind == "stable":
                stable_fixed_point(ax, xv, yv, color=col, name=name.upper())
            else:
                saddle_marker(ax, xv, yv)
    ax.set_xlabel("x"); ax.set_ylabel("y")
    return ax


def demo_potential_2d_heatmap() -> Potential2DInput:
    x = np.linspace(0, 3, 80)
    y = np.linspace(0, 3, 80)
    X, Y = np.meshgrid(x, y)
    centers = np.array([[0.15, 0.15], [0.95, 0.95], [2.25, 2.25]])
    U = 0.1 * (X ** 2 + Y ** 2)
    for cx, cy in centers:
        U = U - 2.5 * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / 0.35)
    gx, gy = np.gradient(-U, x[1] - x[0], y[1] - y[0])
    fps = [(0.15, 0.15, "stable", "home"),
           (0.95, 0.95, "stable", "gate"),
           (2.25, 2.25, "stable", "trap")]
    return Potential2DInput(X=X, Y=Y, U=U, vector_field=(gx, gy), fixed_points=fps)


def waddington_projection(ax, contract, palette: str = "home_gate_trap"):
    """Projected potential surface with optional overlaid cell trajectories."""

    c = WaddingtonInput.model_validate(contract)
    X, Y, U = np.asarray(c.X), np.asarray(c.Y), np.asarray(c.U)
    pal = get_palette(palette)
    hm = ax.imshow(U, origin="lower",
                   extent=(float(X.min()), float(X.max()),
                           float(Y.min()), float(Y.max())),
                   cmap=pal.density, aspect="auto")
    ax.figure.colorbar(hm, ax=ax, shrink=0.85, pad=0.02, label="U")
    if c.trajectories is not None:
        traj = np.asarray(c.trajectories)
        pal_cat = iter_palette(pal.categorical, max(1, traj.shape[0]))
        for i in range(traj.shape[0]):
            ax.plot(traj[i, :, 0], traj[i, :, 1], color=pal_cat[i % len(pal_cat)],
                    linewidth=1.0, alpha=0.9)
    ax.set_xlabel("x"); ax.set_ylabel("y")
    return ax


def demo_waddington_projection() -> WaddingtonInput:
    base = demo_potential_2d_heatmap()
    rng = np.random.default_rng(80)
    n_traj, n_t = 5, 40
    traj = np.zeros((n_traj, n_t, 2))
    for i in range(n_traj):
        traj[i, 0] = rng.uniform([0.0, 0.0], [3.0, 3.0])
        for k in range(1, n_t):
            traj[i, k] = traj[i, k - 1] + rng.normal(0, 0.03, size=2)
    return WaddingtonInput(X=base.X, Y=base.Y, U=base.U, trajectories=traj)


DEMOS = {
    "potential_2d_heatmap": (potential_2d_heatmap, demo_potential_2d_heatmap),
    "waddington_projection": (waddington_projection, demo_waddington_projection),
}
