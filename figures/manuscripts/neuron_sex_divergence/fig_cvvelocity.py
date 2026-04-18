"""Neuron — sex-divergent cv_velocity (stub).

Panel layout (4 → 2×2):
    A  split_violin over sex × genotype
    B  ridge_by_group over sex_geno
    C  coef_forest of mixed-model estimates
    D  paired_slopes (per-animal means)
"""
from __future__ import annotations

from figures.core import close_figure, export_figure, figure_with_grid


def load_inputs() -> dict:
    raise NotImplementedError("load_inputs() must be provided before rendering")


def build_figure():  # pragma: no cover
    inputs = load_inputs()
    fig, axes = figure_with_grid(
        n_panels=4, figsize="double_sq",
        suptitle="Sex-divergent cv_velocity", subtitle="Cdc42 KO in neurons",
        theme="neuron",
    )
    _ = axes, inputs
    return fig


def main() -> None:  # pragma: no cover
    fig = build_figure()
    try:
        export_figure(fig, stem="neuron_sex_divergence_cvvel",
                      theme="neuron", palette="sex_x_genotype",
                      script_path=__file__)
    finally:
        close_figure(fig)


if __name__ == "__main__":  # pragma: no cover
    main()
