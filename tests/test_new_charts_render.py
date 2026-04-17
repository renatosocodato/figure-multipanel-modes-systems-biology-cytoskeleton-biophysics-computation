"""Tests for 5 new chart types introduced in the chart-types expansion.

Coverage:
    phase_portrait       — requires dynamics RHS registry entry
    split_violin         — requires group column with 2 levels + optional animal_id overlay
    ridge_distribution   — requires x + group mappings
    hierarchical_ci_line — requires x + y + group + options.cluster
    sobol_bar            — requires category + y + yerr
"""
from __future__ import annotations
from pathlib import Path

import pytest

from panelforge.charts.registry import registry


NEW_CHART_TYPES = [
    "phase_portrait",
    "split_violin",
    "ridge_distribution",
    "hierarchical_ci_line",
    "sobol_bar",
]


@pytest.mark.parametrize("chart_type", NEW_CHART_TYPES)
def test_new_chart_type_resolves(chart_type: str) -> None:
    """Each new chart type must be registered and resolvable via registry.resolve()."""
    assert registry.resolve(chart_type) is not None


def test_rhoa_dynamics_registry_is_populated() -> None:
    """phase_portrait depends on panelforge.dynamics.RHS_REGISTRY containing rhoa_tristable_v1."""
    from panelforge.dynamics import RHS_REGISTRY, POTENTIAL_REGISTRY

    assert "rhoa_tristable_v1" in RHS_REGISTRY
    assert "rhoa_tristable_v1" in POTENTIAL_REGISTRY

    f = RHS_REGISTRY["rhoa_tristable_v1"]
    # At HOME fixed point (0.15, 0.15), both dx/dt and dy/dt should be ~0
    dx, dy = f([0.15, 0.15])
    assert abs(dx) < 0.1, f"dx/dt at HOME = {dx:.4f}, expected ~0"
    assert abs(dy) < 0.01, f"dy/dt at HOME = {dy:.4f}, expected 0"


def test_rhoa_fixed_points_structure() -> None:
    """HOME-GATE-TRAP landscape must have exactly 3 stable + 2 saddle fixed points."""
    from panelforge.dynamics import rhoa_find_fixed_points

    fps = rhoa_find_fixed_points("basal")
    stable = [fp for fp in fps if fp[1] == "stable"]
    saddles = [fp for fp in fps if fp[1] == "saddle"]
    assert len(stable) == 3, f"Expected 3 stable FPs, got {len(stable)}"
    assert len(saddles) == 2, f"Expected 2 saddles, got {len(saddles)}"


def test_sobol_bar_spec_renders(tmp_path) -> None:
    """Render the Sobol GSA spec end-to-end (Panels A/B use sobol_bar, C hexbin, D regression_ci)."""
    from panelforge.render import render_spec

    repo_root = Path(__file__).resolve().parents[1]
    spec = repo_root / "examples" / "specs" / "m3_sobol_forcebalance.yaml"
    if not spec.exists():
        pytest.skip("Spec not installed at expected path")

    output = render_spec(spec, output_dir=tmp_path / "m3", write_manifest=True)
    panels = output["panels"]
    assert len(panels) == 4
    for panel in panels:
        assert Path(panel["files"]["pdf"]).exists()
        assert Path(panel["files"]["png"]).exists()


def test_neuron_split_violin_and_ridge_render(tmp_path) -> None:
    """Render the Neuron sex-divergence spec (split_violin + ridge_distribution + dot panels)."""
    from panelforge.render import render_spec

    repo_root = Path(__file__).resolve().parents[1]
    spec = repo_root / "examples" / "specs" / "neuron_suppl_cvvel.yaml"
    if not spec.exists():
        pytest.skip("Spec not installed at expected path")

    output = render_spec(spec, output_dir=tmp_path / "neuron", write_manifest=True)
    assert len(output["panels"]) == 4


def test_rhoa_phase_portrait_renders(tmp_path) -> None:
    """Render the RhoA tristability spec including the phase_portrait panel."""
    from panelforge.render import render_spec

    repo_root = Path(__file__).resolve().parents[1]
    spec = repo_root / "examples" / "specs" / "rhoa_landscape.yaml"
    if not spec.exists():
        pytest.skip("Spec not installed at expected path")

    output = render_spec(spec, output_dir=tmp_path / "rhoa", write_manifest=True)
    assert len(output["panels"]) == 4
    assembled = output["assembled"]["files"]
    assert Path(assembled["pdf"]).exists()
    assert Path(assembled["png"]).exists()
