from panelforge.palette.engine import resolve_palette
from panelforge.schema import PaletteSpec


def test_palette_is_deterministic_for_seed() -> None:
    spec = PaletteSpec(seed=42, source="colorbrewer", family="qualitative", palette="Set2", role="primary")
    first = resolve_palette(spec, n_colors=4)
    second = resolve_palette(spec, n_colors=4)
    assert first["palette_hash"] == second["palette_hash"]
    assert first["colors"] == second["colors"]


def test_palette_role_mutates_family_policy() -> None:
    base = PaletteSpec(seed=1, source="colorbrewer", family="qualitative", palette="Set2", role="primary")
    comparison = PaletteSpec(seed=1, source="colorbrewer", family="qualitative", palette="Set2", role="comparison")
    assert resolve_palette(base, 3)["palette_mutation"] != resolve_palette(comparison, 3)["palette_mutation"]
