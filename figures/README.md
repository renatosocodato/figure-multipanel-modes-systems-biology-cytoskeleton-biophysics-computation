# `figures/` — reusable publication-grade figure system

A parallel, bespoke figure production track for manuscripts and grants, built on the same Helvetica-first aesthetic as Panelforge but with richer primitives and data contracts for hero figures.

## What this is

- A **style layer + primitives library + recipe catalog + data-contract layer** that any modeling pipeline (FRET-RhoA ODE, µRedoxScape, cv_velocity mixed models, Sobol GSA, bifurcation, Gillespie, Airyscan morphometry, omics, single-cell) can plug into.
- Manuscript-level scripts (under `manuscripts/`) become **thin 20–60 line callers** on top of this stack.

## Relationship to Panelforge

- **Panelforge** (`panelforge/`) is spec-driven, minimal, and optimized for mixed chart families rendered from YAML specs + manifests. Great for supplementaries and phase-coverage panels.
- **`figures/`** is imperative, opinionated, and optimized for hero figures where every inch counts. The two do not share code or tests; they coexist.

## Quick start

```python
from figures.core import close_figure, export_figure, figure_with_grid
from figures.recipes import RECIPE_REGISTRY

fig, axes = figure_with_grid(
    n_panels=4, figsize="double_sq",
    suptitle="Demo", subtitle="4-panel caller",
)
for ax, name in zip(axes, ["sobol_bar", "split_violin", "phase_portrait", "volcano"]):
    recipe, demo = RECIPE_REGISTRY[name]
    recipe(ax, demo())
export_figure(fig, stem="demo", theme="default", palette="okabe_ito")
close_figure(fig)
```

## Architecture

```
figures/
├── core/        style + palette + primitives + layout + export + contracts
├── recipes/     12 modules (~48 recipes), each with a demo_input()
├── themes/      11 venue themes (nature, cell, pnas, …)
├── manuscripts/ one subdir per paper/grant, with thin callers
├── tests/       isolated pytest suite (not wired into make smoke or CI)
└── outputs/     gitignored render artifacts
```

Layers are unidirectional — `core → recipes → themes → manuscripts` — and every `.py` is importable in isolation.

## Adding a new recipe

1. Pick the correct family module under `figures/recipes/`.
2. Define a Pydantic `Input` subclass in `figures/core/contract.py` (numpy + pandas OK).
3. Write the recipe: `def my_recipe(ax, contract, palette="okabe_ito", **opts) -> ax`. First line: `c = MyInput.model_validate(contract)`.
4. Register a `demo_my_recipe()` builder and add the pair to the module's `DEMOS` dict.
5. `pytest figures/tests/test_recipes_smoke.py -q` will pick it up automatically.

## Adding a new palette

```python
from figures.core.palette import Palette, register_palette

register_palette(Palette(
    name="my_palette",
    categorical=["#112233", ...],         # ≥ 8 entries
    continuous="cividis",                 # colormap name
    diverging="RdBu_r",
    density="magma",
    semantic={"up": "#C62828", "down": "#1976D2"},
))
```

## Adding a new theme

Create `figures/themes/<venue>.py` with `OVERRIDES` dict and `apply(fig=None)`; register in `figures/themes/__init__.py::_THEMES`.

## Adding a new manuscript

Copy `figures/manuscripts/_template_manuscript.py` to a new subdirectory. Keep each caller short — load data, build contracts, dispatch to recipes, export.

## Data contracts

| Family | Contract | Required fields |
|---|---|---|
| sensitivity | `SobolInput` | `parameters`, `S1`, `S1_ci` |
| sensitivity | `MorrisInput` | `parameters`, `mu_star`, `sigma` |
| sensitivity | `RankedContributionInput` | `labels`, `values` |
| sensitivity | `ParameterScanInput` | `x`, `y` |
| sensitivity | `DimensionlessCollapseInput` | `log_x`, `log_y` |
| distributions | `DistributionByGroupInput` | `df`, `value_col`, `group_col` |
| distributions | `RidgeInput` | `df`, `value_col`, `group_col` |
| distributions | `PairedSlopesInput` | `df`, `subject_col`, `condition_col`, `value_col` |
| timecourses | `TimecourseInput` | `df`, `time_col`, `value_col` |
| timecourses | `DoseResponseInput` | `dose`, `response` |
| timecourses | `CalciumRasterInput` | `events` |
| timecourses | `TrajectoryBundleInput` | `t`, `trajectories` |
| regression | `ScatterWithCIInput` | `x`, `y` |
| regression | `BlandAltmanInput` | `a`, `b` |
| regression | `ResidualsInput` | `fitted`, `residuals` |
| regression | `QQInput` | `sample` |
| dynamics | `DynamicsInput` | `rhs_2D` or `U`, `xlim`, `ylim` |
| dynamics | `BifurcationInput` | `r`, `branches` |
| dynamics | `LimitCycleInput` | `t`, `xy` |
| stochastic | `DwellInput` | `df` with state + log10 dwell |
| stochastic | `GillespieInput` | `t`, `trajectories` |
| stochastic | `FPTInput` | `samples` |
| stochastic | `RateScanInput` | `parameter`, `rate` |
| morphometry | `ShapeDistributionInput` | `df`, `metric_col`, `group_col` |
| morphometry | `AiryscanGridInput` | `images` (n, h, w) |
| omics | `VolcanoInput` | `df`, `lfc_col`, `pval_col` |
| omics | `MAInput` | `df`, `m_col`, `a_col` |
| omics | `AnnotatedHeatmapInput` | `matrix`, `row_labels`, `col_labels` |
| omics | `GSEABubbleInput` | `df` with `pathway`, `NES`, `FDR`, `n_genes` |
| omics | `EnrichmentDotInput` | `df` with `ontology`, `term`, `ratio`, `pvalue` |
| embeddings | `UMAPInput` | `embedding`, `metadata` |
| embeddings | `PCABiplotInput` | `scores`, `loadings`, `feature_names` |
| embeddings | `TrajectoryOverlayInput` | `embedding`, `pseudotime` |
| models | `CoefForestInput` | `terms`, `estimate`, `ci_lo`, `ci_hi` |
| models | `PartialDependenceInput` | `grid`, `mean` |
| models | `RandomEffectsInput` | `cluster`, `estimate`, `se` |
| composition | `StackedFractionInput` | `categories`, `components`, `matrix` |
| composition | `TernaryInput` | `abc` (n, 3) |
| composition | `AlluvialInput` | `left_labels`, `right_labels`, `flow_matrix` |
| landscape | `Potential2DInput` | `X`, `Y`, `U` |
| landscape | `WaddingtonInput` | `X`, `Y`, `U` |

## Style guarantees

- Helvetica → Helvetica Neue → Arial → Liberation Sans → DejaVu Sans → sans.
- Type 42 PDF/PS fonts, SVG text kept as glyphs (`svg.fonttype="none"`).
- Base 8.5 pt, ticks 7.5 pt outward, legend 7.5 pt, tile titles 9.5 pt bold.
- Top/right spines hidden; left/bottom `#333333` @ 0.7 pt; no grid; white figure.
- Figure size via named presets (`single`, `single_sq`, `1p5`, `double`, `double_sq`, `tall`, `a4_portrait`, `a4_landscape`).
- Panel labels bold 12 pt at axes-fraction `(-0.17, 1.06)`; tile titles centered, ≤3 words with ellipsis.
- Value labels for error bars always placed right-of-upper-CI.
- Suptitle stack: 12 pt bold @ y=0.985, 9 pt grey @ y=0.955.

## Export formats

- **Default:** vector PDF (Type 42, `Creator` metadata) + high-resolution PNG (`max(spec_dpi, 600)` + `pil_kwargs={"optimize": True}`) on every `export_figure` call.
- On request: SVG (text kept), TIFF, JPEG.
- Optional `{stem}.manifest.json` sibling with script path, git sha, theme, palette, timestamp, input checksums, output checksums.

## Changelog

- **0.1.0** — Initial scaffold (12 recipe modules, 11 themes, 13 palettes, 9 manuscript stubs, isolated test suite).
