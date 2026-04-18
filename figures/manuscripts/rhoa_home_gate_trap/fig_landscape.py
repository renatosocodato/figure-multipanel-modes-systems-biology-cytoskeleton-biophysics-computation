"""RhoA HOME-GATE-TRAP — tristability landscape figure (stub).

Panel layout (4 → 2×2):
    A  phase_portrait
    B  potential_1d
    C  bifurcation
    D  dwell_violin
"""
from __future__ import annotations

from figures.core import close_figure, export_figure, figure_with_grid


def load_inputs() -> dict:
    raise NotImplementedError("load_inputs() must be provided before rendering")


def build_figure():  # pragma: no cover
    inputs = load_inputs()
    fig, axes = figure_with_grid(
        n_panels=4, figsize="double_sq",
        suptitle="RhoA tristability", subtitle="HOME / GATE / TRAP wells",
        theme="cell",
    )
    _ = axes, inputs
    return fig


def main() -> None:  # pragma: no cover
    fig = build_figure()
    try:
        export_figure(fig, stem="rhoa_home_gate_trap_landscape",
                      theme="cell", palette="home_gate_trap",
                      script_path=__file__)
    finally:
        close_figure(fig)


if __name__ == "__main__":  # pragma: no cover
    main()
