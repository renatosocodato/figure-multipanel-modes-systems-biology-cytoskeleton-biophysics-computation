"""µRedoxScape — bimodality figure (stub).

Panel layout (5 → 3×2):
    A  bimodal histogram by condition       (histogram_by_group)
    B  dose_response (paracrine drive)
    C  trajectory_bundle
    D  bifurcation
    E  waddington_projection
"""
from __future__ import annotations

from figures.core import close_figure, export_figure, figure_with_grid


def load_inputs() -> dict:
    raise NotImplementedError("load_inputs() must be provided before rendering")


def build_figure():  # pragma: no cover
    inputs = load_inputs()
    fig, axes = figure_with_grid(
        n_panels=5, figsize="double_sq",
        suptitle="µRedoxScape", subtitle="paracrine bistability landscape",
        theme="cell",
    )
    _ = axes, inputs
    return fig


def main() -> None:  # pragma: no cover
    fig = build_figure()
    try:
        export_figure(fig, stem="uredoxscape_bimodality",
                      theme="cell", palette="redox_bistable",
                      script_path=__file__)
    finally:
        close_figure(fig)


if __name__ == "__main__":  # pragma: no cover
    main()
