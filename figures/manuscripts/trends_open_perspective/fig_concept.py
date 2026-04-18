"""Trends Open perspective — concept figure (stub). Review-style full-page."""
from __future__ import annotations

from figures.core import close_figure, export_figure, figure_with_grid


def load_inputs() -> dict:
    raise NotImplementedError("load_inputs() must be provided before rendering")


def build_figure():  # pragma: no cover
    inputs = load_inputs()
    fig, axes = figure_with_grid(
        n_panels=4, figsize="double_sq",
        suptitle="Cytoskeletal decisions", subtitle="concept figure",
        theme="trends",
    )
    _ = axes, inputs
    return fig


def main() -> None:  # pragma: no cover
    fig = build_figure()
    try:
        export_figure(fig, stem="trends_concept",
                      theme="trends", palette="rhogtpase_family",
                      script_path=__file__)
    finally:
        close_figure(fig)


if __name__ == "__main__":  # pragma: no cover
    main()
