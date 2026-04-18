"""FRET-RhoA v4.3 — scaffold overview figure (stub).

Intended panel layout (5 panels → 3×2 grid):
    A  biosensor schematic                 (external SVG embed)
    B  donor/acceptor time traces          (recipes.timecourses.fret_traces)
    C  FRET ratio by condition             (recipes.distributions.beeswarm_by_group)
    D  phase portrait of ODE model         (recipes.dynamics.phase_portrait)
    E  parameter scan + reference line     (recipes.sensitivity.parameter_scan_hexbin)

Fill the contract builders below with live data when available.
"""
from __future__ import annotations

from figures.core import close_figure, export_figure, figure_with_grid


def load_inputs() -> dict:
    """Replace with real loader (CSV/Parquet/Feather or modeling-layer output)."""

    raise NotImplementedError("load_inputs() must be provided before rendering")


def build_figure():  # pragma: no cover — invoked only when data is present
    inputs = load_inputs()
    fig, axes = figure_with_grid(
        n_panels=5, figsize="double_sq",
        suptitle="FRET-RhoA v4.3", subtitle="biosensor → dynamics overview",
        theme="cell",
    )
    _ = axes, inputs  # recipe dispatch lives here
    return fig


def main() -> None:  # pragma: no cover
    fig = build_figure()
    try:
        export_figure(fig, stem="fret_rhoa_v43_overview",
                      theme="cell", palette="fret_donor_acceptor",
                      script_path=__file__)
    finally:
        close_figure(fig)


if __name__ == "__main__":  # pragma: no cover
    main()
