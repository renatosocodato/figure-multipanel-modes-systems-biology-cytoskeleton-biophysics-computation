"""Compositional recipes.

Contains:
    stacked_fraction         — 100 % stacked bars with in-bar fraction labels
    composition_triangle     — ternary scatter for 3-component compositions
    alluvial_like            — simple flow diagram built with fill_between
"""
from __future__ import annotations

import numpy as np

from ..core.contract import AlluvialInput, StackedFractionInput, TernaryInput
from ..core.palette import get_palette
from ..core.primitives import halo_text, iter_palette


def stacked_fraction(ax, contract, palette: str = "okabe_ito"):
    """100 % stacked horizontal bars with labels above 0.06 of the width."""

    c = StackedFractionInput.model_validate(contract)
    matrix = np.asarray(c.matrix, dtype=float)
    if matrix.shape != (len(c.categories), len(c.components)):
        raise ValueError("matrix shape must be (len(categories), len(components))")
    row_sums = matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    norm = matrix / row_sums
    pal = iter_palette(get_palette(palette).categorical, len(c.components))
    y = np.arange(len(c.categories))
    left = np.zeros(len(c.categories))
    for j, comp in enumerate(c.components):
        widths = norm[:, j]
        ax.barh(y, widths, left=left, color=pal[j], edgecolor="white",
                linewidth=0.4, label=str(comp))
        for i, w in enumerate(widths):
            if w >= 0.06:
                halo_text(ax, left[i] + w / 2, y[i], f"{w * 100:.0f}%",
                          color="white", fontsize=7, fontweight="bold")
        left += widths
    ax.set_yticks(y)
    ax.set_yticklabels([str(x) for x in c.categories])
    ax.set_xlim(0, 1)
    ax.set_xlabel("fraction")
    ax.legend(fontsize=7, frameon=False, ncol=min(len(c.components), 4),
              loc="upper center", bbox_to_anchor=(0.5, 1.2))
    return ax


def demo_stacked_fraction() -> StackedFractionInput:
    return StackedFractionInput(
        categories=["ctrl", "drug1", "drug2", "KO"],
        components=["home", "gate", "trap"],
        matrix=np.array([
            [0.60, 0.30, 0.10],
            [0.35, 0.45, 0.20],
            [0.40, 0.20, 0.40],
            [0.20, 0.30, 0.50],
        ]),
    )


def composition_triangle(ax, contract, palette: str = "home_gate_trap"):
    """Ternary scatter: each row plots as a simplex coordinate."""

    c = TernaryInput.model_validate(contract)
    abc = np.asarray(c.abc, dtype=float)
    if abc.shape[1] != 3:
        raise ValueError("abc must be (n, 3)")
    # Project simplex to 2D Cartesian.
    x = 0.5 * (2 * abc[:, 1] + abc[:, 2]) / abc.sum(axis=1)
    y = (np.sqrt(3) / 2) * abc[:, 2] / abc.sum(axis=1)
    pal = iter_palette(get_palette(palette).categorical, 3)
    ax.scatter(x, y, color=pal[0], s=14, alpha=0.7, edgecolor="white", linewidth=0.3)
    # Draw triangle frame.
    ax.plot([0, 1, 0.5, 0], [0, 0, np.sqrt(3) / 2, 0], color="#111", linewidth=0.8)
    halo_text(ax, 0, -0.04, c.labels[0], color="#111", fontsize=8, ha="center")
    halo_text(ax, 1, -0.04, c.labels[1], color="#111", fontsize=8, ha="center")
    halo_text(ax, 0.5, np.sqrt(3) / 2 + 0.04, c.labels[2], color="#111",
              fontsize=8, ha="center")
    ax.set_axis_off()
    ax.set_aspect("equal")
    return ax


def demo_composition_triangle() -> TernaryInput:
    rng = np.random.default_rng(70)
    raw = rng.dirichlet([2.0, 1.5, 1.0], size=80)
    return TernaryInput(abc=raw, labels=("HOME", "GATE", "TRAP"))


def alluvial_like(ax, contract, palette: str = "okabe_ito"):
    """Two-column flow diagram using fill_between polygons."""

    c = AlluvialInput.model_validate(contract)
    flow = np.asarray(c.flow_matrix, dtype=float)
    if flow.shape != (len(c.left_labels), len(c.right_labels)):
        raise ValueError("flow_matrix shape mismatch")
    pal = iter_palette(get_palette(palette).categorical, 12)
    left_totals = flow.sum(axis=1)
    right_totals = flow.sum(axis=0)
    total = max(flow.sum(), 1e-9)

    y_left = np.concatenate(([0.0], np.cumsum(left_totals) / total))
    y_right = np.concatenate(([0.0], np.cumsum(right_totals) / total))

    pos_left = y_left.copy()
    pos_right = y_right.copy()
    for i in range(len(c.left_labels)):
        running_left = y_left[i]
        for j in range(len(c.right_labels)):
            flow_amt = flow[i, j] / total
            if flow_amt <= 0:
                continue
            top_left_a = running_left
            top_left_b = running_left + flow_amt
            running_left = top_left_b
            top_right_a = pos_right[j]
            top_right_b = pos_right[j] + flow_amt
            pos_right[j] = top_right_b
            xs = np.linspace(0, 1, 40)
            def _smooth(a, b):
                return a + (b - a) * 0.5 * (1 - np.cos(np.pi * xs))
            lower = _smooth(top_left_a, top_right_a)
            upper = _smooth(top_left_b, top_right_b)
            ax.fill_between(xs, lower, upper, color=pal[(i + j) % len(pal)],
                            alpha=0.55, linewidth=0)
    for i, lbl in enumerate(c.left_labels):
        ax.text(-0.02, (y_left[i] + y_left[i + 1]) / 2, str(lbl),
                fontsize=7, ha="right", va="center")
    for j, lbl in enumerate(c.right_labels):
        ax.text(1.02, (y_right[j] + y_right[j + 1]) / 2, str(lbl),
                fontsize=7, ha="left", va="center")
    ax.set_xlim(-0.2, 1.2); ax.set_ylim(0, 1.02)
    ax.set_axis_off()
    _ = pos_left  # reserved for downstream label polish
    return ax


def demo_alluvial_like() -> AlluvialInput:
    rng = np.random.default_rng(71)
    left = ["clone A", "clone B", "clone C"]
    right = ["DAM1", "DAM2", "homeostatic"]
    flow = rng.dirichlet([2, 2, 2], size=len(left)).cumsum(axis=1)[:, ::-1]
    flow = np.asarray(flow)
    return AlluvialInput(left_labels=left, right_labels=right, flow_matrix=flow)


DEMOS = {
    "stacked_fraction": (stacked_fraction, demo_stacked_fraction),
    "composition_triangle": (composition_triangle, demo_composition_triangle),
    "alluvial_like": (alluvial_like, demo_alluvial_like),
}
