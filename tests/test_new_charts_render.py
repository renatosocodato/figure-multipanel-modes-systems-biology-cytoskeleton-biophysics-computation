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


def test_phase_portrait_honours_custom_xy_mappings() -> None:
    """phase_portrait must read coordinates through mappings.x/mappings.y, not hardcoded 'x'/'y'."""
    import pandas as pd

    from panelforge.charts.base import RenderContext
    from panelforge.charts.bivariate import render_phase_portrait

    data = pd.DataFrame(
        {
            "state": ["home", "gate", "trap"],
            "rhoa": [0.15, 0.95, 2.25],
            "p190": [0.15, 0.95, 2.25],
            "stability": ["stable", "stable", "stable"],
        }
    )
    ctx = RenderContext(
        data=data,
        chart_spec={
            "mappings": {"x": "rhoa", "y": "p190", "category": "state"},
            "options": {
                "xlim": [0.0, 3.0],
                "ylim": [0.0, 3.0],
                "grid": 6,
                "rhs": "rhoa_tristable_v1",
                "cond": "basal",
                "nullclines": False,
            },
        },
        palette=["#111111"],
        width=3.0,
        height=2.4,
    )
    fig, ax = render_phase_portrait(ctx, panel=None)
    assert fig is not None and ax is not None


def test_split_violin_falls_back_for_non_binary_groups() -> None:
    """Three-level group must not raise; render falls back to unsplit with a warning."""
    import pandas as pd

    from panelforge.charts.base import RenderContext
    from panelforge.charts.univariate import render_split_violin

    data = pd.DataFrame(
        {
            "x": ["a"] * 15,
            "y": list(range(15)),
            "g": (["g1"] * 5 + ["g2"] * 5 + ["g3"] * 5),
        }
    )
    ctx = RenderContext(
        data=data,
        chart_spec={"mappings": {"x": "x", "y": "y", "group": "g"}, "options": {}},
        palette=["#D55E00", "#0072B2"],
        width=3.0,
        height=2.4,
    )
    fig, ax = render_split_violin(ctx, panel=None)
    warning_texts = [t.get_text() for t in ax.texts if "needs 2 group levels" in t.get_text()]
    assert warning_texts, "fallback warning pill should be rendered"


def test_phase_portrait_respects_options_potential_override() -> None:
    """options.potential must select the contour backdrop independently of options.rhs."""
    import pandas as pd

    from panelforge.charts.base import RenderContext
    from panelforge.charts.bivariate import render_phase_portrait

    data = pd.DataFrame(
        {"state": ["home"], "x": [0.15], "y": [0.15], "stability": ["stable"]}
    )
    base_spec = {
        "mappings": {"x": "x", "y": "y"},
        "options": {
            "xlim": [0.0, 3.0],
            "ylim": [0.0, 3.0],
            "grid": 6,
            "rhs": "rhoa_tristable_v1",
            "cond": "basal",
            "nullclines": False,
        },
    }

    # Baseline: backdrop present (countourf draws one collection).
    ctx_default = RenderContext(data=data, chart_spec=base_spec, palette=["#111"], width=3.0, height=2.4)
    _, ax_default = render_phase_portrait(ctx_default, panel=None)
    default_collections = len(ax_default.collections)

    # Explicit override to disable: fewer collections than the default backdrop case.
    override_spec = {**base_spec, "options": {**base_spec["options"], "potential": "none"}}
    ctx_off = RenderContext(data=data, chart_spec=override_spec, palette=["#111"], width=3.0, height=2.4)
    _, ax_off = render_phase_portrait(ctx_off, panel=None)
    assert len(ax_off.collections) < default_collections, (
        "options.potential='none' should suppress the contour backdrop"
    )


def test_hierarchical_ci_sem_uses_per_bin_cluster_count() -> None:
    """SEM denominator must be the observed cluster count at each x-bin, not total columns."""
    import numpy as np
    import pandas as pd

    from panelforge.charts.base import RenderContext
    from panelforge.charts.bivariate import render_hierarchical_ci_line

    # 3 clusters total, but only cluster A exists at t=0 (should yield NaN SEM),
    # and all three exist at t=1 (SEM divides by sqrt(3), not a larger denom).
    rows = [
        {"animal_id": "A", "t": 0, "y": 1.0, "grp": "g1"},
        {"animal_id": "A", "t": 1, "y": 2.0, "grp": "g1"},
        {"animal_id": "B", "t": 1, "y": 3.0, "grp": "g1"},
        {"animal_id": "C", "t": 1, "y": 4.0, "grp": "g1"},
    ]
    data = pd.DataFrame(rows)
    ctx = RenderContext(
        data=data,
        chart_spec={
            "mappings": {"x": "t", "y": "y", "group": "grp"},
            "options": {"cluster": "animal_id"},
        },
        palette=["#0072B2"],
        width=3.0,
        height=2.4,
    )
    fig, ax = render_hierarchical_ci_line(ctx, panel=None)

    fills = [c for c in ax.collections if hasattr(c, "get_paths")]
    assert fills, "expected a fill_between CI band"
    verts = np.concatenate([p.vertices for p in fills[0].get_paths()])
    ys = verts[:, 1]
    # At t=0 the band collapses (single cluster -> NaN SEM -> no finite band).
    # At t=1 the band is finite; width must equal 1.96 * std/sqrt(3) * 2.
    std_t1 = float(np.std([2.0, 3.0, 4.0], ddof=1))
    expected_half_width = 1.96 * std_t1 / np.sqrt(3)
    finite = ys[np.isfinite(ys)]
    observed_half_width = (finite.max() - finite.min()) / 2.0
    assert np.isclose(observed_half_width, expected_half_width, rtol=1e-3), (
        f"expected half-width {expected_half_width:.4f} for 3 clusters, got {observed_half_width:.4f}"
    )
