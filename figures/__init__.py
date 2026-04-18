"""Reusable publication-grade figure system.

Layered as `core → recipes → themes → manuscripts`. Each manuscript caller is
a thin script that assembles data, builds contracts, dispatches to recipes,
and exports through :func:`figures.core.export.export_figure`.

See ``figures/README.md`` for the full architecture and style guarantees.
"""
from __future__ import annotations

__all__ = ["__version__"]
__version__ = "0.1.0"
