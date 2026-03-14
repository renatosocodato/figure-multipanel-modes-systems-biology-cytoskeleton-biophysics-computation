Universal Multipanel Figure Factory
=================================

`panelforge` is a schema-first, reusable figure pipeline for analysis repos that
need scalable multipanel outputs across biology, cytoskeleton biophysics, and
computational biology projects.

It supports:

- A permissive chart contract for Python and R rendering.
- Mandatory high-resolution PNG + vector PDF panel outputs.
- Global minimal Arial-based styling with panel tile metadata.
- Wide-scope discovery and diagnostics across `/Users/renatosocodato`.
- Palette mutation metadata and manifest reproducibility records.
- Legacy adapters for existing 4-panel and supplementary R workflows.

## Repository Layout

- `panelforge/`: Core Python package.
- `R/panel_renderer.R`: Minimal ggplot2-compatible renderer with shared schema
  contracts.
- `examples/specs/`: Spec templates.
- `examples/templates/`: Small manifest and run examples.
- `tests/`: Unit tests for schema, transforms, registry and render contract.
- `.github/workflows/`: CI with Python + R smoke checks.

## Installation

```bash
cd figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -e .
```

## CLI

```bash
panelforge discover --roots /Users/renatosocodato --output discovery.json
panelforge inspect examples/specs/single_panel.yaml
panelforge render examples/specs/legacy_4panel.yaml --out /tmp/figures
panelforge tile examples/specs/single_panel.yaml
panelforge manifest /tmp/figures/figure/run_manifest.json --output /tmp/figures/manifest.json
```

Legacy bridges:

```bash
panelforge render-legacy-main --paper-root /path/to/paper --phase 1 --out /tmp/figures
panelforge render-legacy-supplementary --paper-root /path/to/paper --phase 1 --panel-label S1 --out /tmp/figures
```

## Spec format (minimal)

```yaml
title: "Figure title"
subtitle: "Figure-level subtitle"
layout:
  preset: C
panels:
  - label: "A"
    title: "Panel title"
    subtitle: "Panel subtitle"
    tile:
      label: "A"
      title: "Tile title"
      subtitle: "Tile subtitle"
      status: "ok"
      outcome: "pass"
    chart:
      chart_type: scatter
      data:
        path: "data.csv"
        format: "csv"
      mappings:
        x: "x"
        y: "y"
        group: "group"
render:
  formats: ["pdf", "png"]
  dpi: 600
  width: 8.0
  height: 6.0
```

Mandatory behavior:

- Figure and panel subtitles are emitted into panel tiles.
- Every rendered panel gets both:
  - `*.pdf` (vector)
  - `*.png` (at least 600 DPI)
- Every run can emit `run_manifest.json` with checksums.

## Python package API

- `panelforge.schema`: pydantic schema models (versioned).
- `panelforge.render.render_spec(...)`: programmatic rendering entry.
- `panelforge.discovery.phase_discovery(...)`: discovery of `analysis_*` directories.
- `panelforge.palette.resolve_palette(...)`: ColorBrewer-backed palette contract.

## R renderer

`R/panel_renderer.R` accepts the same YAML specification and writes PDF+PNG files
for each panel. It includes a minimal Arial theme and tile annotations.

## Tests and CI

```bash
pytest -q
```

CI runs:

- Schema validation and transform tests (Python)
- Chart registry smoke tests (Python)
- Minimal R smoke render of one template

## Versioning

Schema: `1.0.0`
