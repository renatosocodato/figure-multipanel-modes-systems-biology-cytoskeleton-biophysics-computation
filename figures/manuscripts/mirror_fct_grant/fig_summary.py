"""MIRROR FCT grant — project summary figure (stub). A4 portrait."""
from __future__ import annotations

from figures.core import close_figure, export_figure, figure_with_grid


def load_inputs() -> dict:
    raise NotImplementedError("load_inputs() must be provided before rendering")


def build_figure():  # pragma: no cover
    inputs = load_inputs()
    fig, axes = figure_with_grid(
        n_panels=6, figsize="a4_portrait",
        suptitle="MIRROR project", subtitle="aims summary",
        theme="fct_grant",
    )
    _ = axes, inputs
    return fig


def main() -> None:  # pragma: no cover
    fig = build_figure()
    try:
        export_figure(fig, stem="mirror_fct_summary",
                      theme="fct_grant", palette="microglia_states",
                      script_path=__file__)
    finally:
        close_figure(fig)


if __name__ == "__main__":  # pragma: no cover
    main()
