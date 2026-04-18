"""Semantic palette registry.

Contract
--------
Every palette is a :class:`Palette` carrying four colormap-style fields
(``categorical`` list, ``continuous``/``diverging``/``density`` colormap
names) and a ``semantic`` dict mapping research-meaningful aliases to hex
strings. Palettes are registered on import; downstream code adds more via
:func:`register_palette` without touching existing ones.

Example
-------
>>> from figures.core.palette import get_palette, semantic
>>> okabe = get_palette("okabe_ito")
>>> okabe.categorical[0]
'#E69F00'
>>> semantic("home_gate_trap", "home")
'#1B5E20'
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Palette(BaseModel):
    """A named palette with categorical, continuous, diverging, and semantic layers."""

    name: str
    categorical: List[str] = Field(min_length=8)
    continuous: str = "viridis"
    diverging: str = "RdBu_r"
    density: str = "magma"
    semantic: Dict[str, str] = Field(default_factory=dict)


_REGISTRY: Dict[str, Palette] = {}


def register_palette(palette: Palette) -> None:
    """Add or replace a palette. Names are case-insensitive."""

    if not isinstance(palette, Palette):
        raise TypeError(f"expected Palette, got {type(palette).__name__}")
    _REGISTRY[palette.name.lower()] = palette


def get_palette(name: str) -> Palette:
    """Look up a palette by name; raises ``KeyError`` with a helpful list."""

    key = str(name).lower()
    if key not in _REGISTRY:
        raise KeyError(f"unknown palette {name!r}; known: {sorted(_REGISTRY)}")
    return _REGISTRY[key]


def list_palettes() -> List[str]:
    """Return all registered palette names in insertion order."""

    return list(_REGISTRY)


def semantic(palette_name: str, alias: str, default: Optional[str] = None) -> str:
    """Resolve a semantic alias to a hex color within a named palette."""

    pal = get_palette(palette_name)
    if alias in pal.semantic:
        return pal.semantic[alias]
    if default is not None:
        return default
    raise KeyError(
        f"palette {palette_name!r} has no semantic alias {alias!r}; known: {sorted(pal.semantic)}"
    )


# ---------------------------------------------------------------------------
# Required palettes — registered on import per the brief.
# ---------------------------------------------------------------------------

_OKABE = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermilion
    "#CC79A7",  # reddish purple
    "#000000",  # black
]


_BASE_PALETTES: List[Palette] = [
    Palette(
        name="okabe_ito",
        categorical=_OKABE,
        continuous="viridis",
        diverging="RdBu_r",
        density="magma",
        semantic={},
    ),
    Palette(
        name="sex_dimorphic",
        categorical=["#C2185B", "#1976D2", "#6A1B9A", "#616161"] + _OKABE[:4],
        continuous="cividis",
        diverging="PuOr",
        density="magma",
        semantic={
            "female": "#C2185B",
            "male": "#1976D2",
            "intersex": "#6A1B9A",
            "unknown": "#616161",
        },
    ),
    Palette(
        name="home_gate_trap",
        categorical=["#1B5E20", "#F9A825", "#C62828", "#455A64"] + _OKABE[:4],
        continuous="cividis",
        diverging="RdYlGn",
        density="magma",
        semantic={
            "home": "#1B5E20",
            "gate": "#F9A825",
            "trap": "#C62828",
            "basal": "#0072B2",
            "rocki": "#D55E00",
            "srci": "#6A1B9A",
        },
    ),
    Palette(
        name="wt_ko",
        categorical=["#455A64", "#C62828", "#1565C0", "#6A1B9A", "#F9A825"] + _OKABE[:3],
        continuous="viridis",
        diverging="RdBu_r",
        density="magma",
        semantic={
            "wt": "#455A64",
            "ko": "#C62828",
            "het": "#F9A825",
            "rescue": "#1565C0",
            "drug": "#6A1B9A",
        },
    ),
    Palette(
        name="redox_bistable",
        categorical=["#1976D2", "#D84315", "#6A1B9A", "#009E73"] + _OKABE[:4],
        continuous="cividis",
        diverging="RdBu_r",
        density="inferno",
        semantic={
            "reduced": "#1976D2",
            "oxidized": "#D84315",
            "bistable": "#6A1B9A",
            "paracrine": "#009E73",
        },
    ),
    Palette(
        name="fret_donor_acceptor",
        categorical=["#1976D2", "#C2185B", "#6A1B9A", "#424242"] + _OKABE[:4],
        continuous="viridis",
        diverging="RdBu_r",
        density="magma",
        semantic={
            "donor": "#1976D2",
            "acceptor": "#C2185B",
            "fret_ratio": "#6A1B9A",
            "unfret": "#424242",
        },
    ),
    Palette(
        name="sex_x_genotype",
        categorical=["#EC407A", "#AD1457", "#42A5F5", "#1565C0"] + _OKABE[:4],
        continuous="cividis",
        diverging="PuOr",
        density="magma",
        semantic={
            "female_wt": "#EC407A",
            "female_ko": "#AD1457",
            "male_wt": "#42A5F5",
            "male_ko": "#1565C0",
        },
    ),
    Palette(
        name="timepoint_gradient",
        categorical=["#00224E", "#2C5F84", "#6C9CB0", "#D4D4A3", "#FDE725"] + _OKABE[:3],
        continuous="cividis",
        diverging="RdBu_r",
        density="cividis",
        semantic={
            "baseline": "#00224E",
            "early": "#2C5F84",
            "peak": "#6C9CB0",
            "recovery": "#FDE725",
        },
    ),
    Palette(
        name="mechanism_class",
        categorical=["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#F0E442"] + _OKABE[:3],
        continuous="viridis",
        diverging="RdBu_r",
        density="magma",
        semantic={
            "polymerization": "#0072B2",
            "contractility": "#D55E00",
            "adhesion": "#009E73",
            "signaling": "#CC79A7",
            "membrane": "#F0E442",
        },
    ),
    Palette(
        name="cytoskeleton_components",
        categorical=["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD", "#8C564B"] + _OKABE[:2],
        continuous="viridis",
        diverging="RdBu_r",
        density="magma",
        semantic={
            "actin": "#1F77B4",
            "microtubule": "#FF7F0E",
            "intermediate": "#2CA02C",
            "myosin": "#D62728",
            "arp23": "#9467BD",
            "formin": "#8C564B",
        },
    ),
    Palette(
        name="rhogtpase_family",
        categorical=["#C62828", "#1565C0", "#2E7D32", "#F9A825", "#6A1B9A"] + _OKABE[:3],
        continuous="viridis",
        diverging="RdBu_r",
        density="magma",
        semantic={
            "rhoa": "#C62828",
            "rac1": "#1565C0",
            "cdc42": "#2E7D32",
            "rhob": "#F9A825",
            "rhoc": "#6A1B9A",
        },
    ),
    Palette(
        name="microglia_states",
        categorical=["#455A64", "#FB8C00", "#C62828", "#AD1457", "#6A1B9A"] + _OKABE[:3],
        continuous="cividis",
        diverging="RdBu_r",
        density="inferno",
        semantic={
            "homeostatic": "#455A64",
            "primed": "#FB8C00",
            "dam1": "#C62828",
            "dam2": "#AD1457",
            "senescent": "#6A1B9A",
        },
    ),
    Palette(
        name="journal_neutral",
        categorical=["#37474F", "#546E7A", "#78909C", "#90A4AE", "#B0BEC5", "#CFD8DC", "#263238", "#455A64"],
        continuous="gray",
        diverging="RdBu_r",
        density="gray",
        semantic={},
    ),
]


for _p in _BASE_PALETTES:
    register_palette(_p)
