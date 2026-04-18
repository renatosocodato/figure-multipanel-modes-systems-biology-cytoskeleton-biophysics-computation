"""Manuscript 3 — Sobol GSA on the force-balance ODE (stub).

Panel layout (4 → 2×2):
    A  sobol_bar (S1)
    B  sobol_bar (ST)
    C  parameter_scan_hexbin
    D  dimensionless_collapse
"""
from __future__ import annotations

from figures.core import close_figure, export_figure, figure_with_grid


def load_inputs() -> dict:
    raise NotImplementedError("load_inputs() must be provided before rendering")


def build_figure():  # pragma: no cover
    inputs = load_inputs()
    fig, axes = figure_with_grid(
        n_panels=4, figsize="double_sq",
        suptitle="Process length sensitivity", subtitle="Sobol GSA on force balance",
        theme="bpj",
    )
    _ = axes, inputs
    return fig


def main() -> None:  # pragma: no cover
    fig = build_figure()
    try:
        export_figure(fig, stem="m3_sobol_forcebalance",
                      theme="bpj", palette="mechanism_class",
                      script_path=__file__)
    finally:
        close_figure(fig)


if __name__ == "__main__":  # pragma: no cover
    main()
