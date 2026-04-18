"""Palette registry contract — all required palettes registered, register_palette round-trips."""
from __future__ import annotations

import pytest

from figures.core.palette import (
    Palette,
    get_palette,
    list_palettes,
    register_palette,
    semantic,
)


REQUIRED_PALETTES = [
    "okabe_ito",
    "sex_dimorphic",
    "home_gate_trap",
    "wt_ko",
    "redox_bistable",
    "fret_donor_acceptor",
    "sex_x_genotype",
    "timepoint_gradient",
    "mechanism_class",
    "cytoskeleton_components",
    "rhogtpase_family",
    "microglia_states",
    "journal_neutral",
]


@pytest.mark.parametrize("name", REQUIRED_PALETTES)
def test_required_palette_is_registered(name: str) -> None:
    pal = get_palette(name)
    assert isinstance(pal, Palette)
    assert len(pal.categorical) >= 8
    for color in pal.categorical:
        assert color.startswith("#") and len(color) in {7, 9}


def test_semantic_lookup_resolves_known_aliases() -> None:
    assert semantic("home_gate_trap", "home").startswith("#")
    assert semantic("sex_dimorphic", "female").startswith("#")


def test_semantic_unknown_alias_raises() -> None:
    with pytest.raises(KeyError):
        semantic("home_gate_trap", "not_a_state")


def test_register_palette_round_trips() -> None:
    pal = Palette(name="smoke_test", categorical=["#000000"] * 8,
                  continuous="viridis", diverging="RdBu_r",
                  density="magma", semantic={"marker": "#111111"})
    register_palette(pal)
    assert "smoke_test" in list_palettes()
    assert semantic("smoke_test", "marker") == "#111111"
