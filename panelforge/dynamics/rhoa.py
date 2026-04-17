"""RhoA HOME-GATE-TRAP tristability dynamics.

U(x) is a three-well quasi-potential (three Gaussian wells + weak quadratic confinement).
2D extension for phase_portrait: dx/dt = -dU/dx, dy/dt = k_y * (x - y).

This module is the single source of truth for:
  * Panel A phase_portrait (vector field comes from rhoa_tristable_v1)
  * Panel B potential U (from U(x, cond))
  * Panel C bifurcation (analytical branches via dU/dx root-tracking)
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import brentq

CENTERS = np.array([0.15, 0.95, 2.25])
WIDTHS = np.array([0.20, 0.28, 0.32])
WEIGHTS_BASAL = np.array([2.50, 2.60, 2.80])
K_QUADRATIC = 0.10

MODULATION = {
    "basal": np.array([1.00, 1.00, 1.00]),
    "ROCKi": np.array([0.88, 1.30, 1.00]),  # destabilizes HOME, deepens GATE
    "SRCi":  np.array([1.00, 1.00, 0.62]),  # shallows TRAP, enables exit
}


def weights(cond: str = "basal") -> np.ndarray:
    return WEIGHTS_BASAL * MODULATION.get(cond, np.ones(3))


def U(x, cond: str = "basal"):
    """Three-well quasi-potential U(x; cond)."""
    w = weights(cond)
    x = np.asarray(x, dtype=float)
    return K_QUADRATIC * x**2 - sum(
        w[i] * np.exp(-((x - CENTERS[i]) / WIDTHS[i])**2) for i in range(3)
    )


def dU_dx(x, cond: str = "basal"):
    """Analytical gradient of U."""
    w = weights(cond)
    x = np.asarray(x, dtype=float)
    grad = 2 * K_QUADRATIC * x
    for i in range(3):
        s = WIDTHS[i]
        grad += (w[i] * 2 * (x - CENTERS[i]) / s**2
                 * np.exp(-((x - CENTERS[i]) / s)**2))
    return grad


def rhoa_tristable_v1(state, cond: str = "basal", k_y: float = 0.8):
    """2D RHS for phase_portrait: dx = -dU/dx, dy = k_y*(x - y).

    Accepts state = [x, y] or (x, y).
    Returns [dx, dy].
    """
    x, y = state
    return [float(-dU_dx(x, cond)), float(k_y * (x - y))]


def U_2D(x, y, cond: str = "basal", lam: float = 0.45):
    """2D extension: U_2D(x,y) = U(x) + 0.5*lam*(x-y)^2.

    Minima on the line y = x at the roots of dU/dx.
    """
    return U(x, cond) + 0.5 * lam * (x - y)**2


def find_fixed_points(cond: str = "basal"):
    """Locate all roots of dU/dx on [0, 3] by sign-change bracketing.

    Returns list of (x*, kind) with kind in {"stable", "saddle"}.
    """
    grid = np.linspace(0.001, 3.0, 800)
    vals = dU_dx(grid, cond)
    roots = []
    for i in range(len(grid) - 1):
        if vals[i] * vals[i + 1] < 0:
            r = brentq(lambda z: dU_dx(z, cond), grid[i], grid[i + 1])
            h = 1e-5
            d2 = (dU_dx(r + h, cond) - dU_dx(r - h, cond)) / (2 * h)
            roots.append((r, "stable" if d2 > 0 else "saddle"))
    return roots


def analytical_bifurcation(n: int = 200, r_sn: float = 0.45):
    """Analytical saddle-node bifurcation branches for illustrative Panel C.

    HOME (stable) and the HG saddle collide at r = r_sn. Beyond r_sn only the
    GATE / TRAP branches remain (bistable regime).
    """
    r = np.linspace(0.0, 1.0, n)
    frac = np.clip(r / r_sn, 0.0, 1.0)
    mask = r < r_sn
    x_home = np.where(mask, 0.15 + 0.17 * frac**2, np.nan)
    x_hgs = np.where(mask, 0.50 - 0.18 * frac**2, np.nan)
    x_gate = 0.95 + 0.08 * r
    x_gts = 1.60 - 0.04 * r
    x_trap = np.full_like(r, 2.25)
    return {
        "r": r, "r_sn": r_sn,
        "home": x_home, "hgs": x_hgs,
        "gate": x_gate, "gts": x_gts, "trap": x_trap,
    }
