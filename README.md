# Panelforge

[![CI](https://github.com/renatosocodato/figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation/actions/workflows/ci.yml/badge.svg)](https://github.com/renatosocodato/figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/renatosocodato/figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation)](https://github.com/renatosocodato/figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation/releases)
[![License](https://img.shields.io/github/license/renatosocodato/figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation)](LICENSE)

Schema-first multipanel figure generation for systems biology, cytoskeleton biophysics, and computational biology workflows.

`panelforge` is built to be cloned into analysis repositories when the modeling layer is ready to become figures. It keeps the interface simple, the defaults strict where they matter, and the rendering behavior permissive where real analysis pipelines tend to be messy.

## Why it is easy to clone

- One bootstrap command creates the local environment and installs the package.
- One smoke command validates Python tests and example renders.
- One schema powers both Python and R renderers.
- Every panel and assembled figure emits `pdf` and `png` by default.
- Tile metadata, subtitles, manifests, and palette fingerprints are built in.

## Quick start

```bash
git clone https://github.com/renatosocodato/figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation.git
cd figure-multipanel-modes-systems-biology-cytoskeleton-biophysics-computation
make bootstrap
make demo-single
make demo-four
make smoke
```

If you want a fast orientation first:

```bash
make help
```

## First-run outputs

After the demo commands you will have both per-panel and assembled figure artifacts under `outputs/`.

```text
outputs/
├── single/
│   ├── single_panel_hist.pdf
│   ├── single_panel_hist.png
│   ├── single_panel.pdf
│   ├── single_panel.png
│   └── render_manifest.json
└── four/
    ├── four_panel_scatter.pdf
    ├── four_panel_heatmap.png
    ├── four_panel.pdf
    ├── four_panel.png
    └── render_manifest.json
```

## Repo shape

```text
.
├── panelforge/      Python package: schema, charts, renderers, manifests, CLI
├── R/               ggplot2-based renderer with the same figure contract
├── examples/        data, specs, and starter templates
├── scripts/         bootstrap and smoke helpers for local clones
├── tests/           schema, palette, render, transform, and CLI coverage
├── .github/         CI plus issue and PR templates
├── Makefile         memorable local commands
└── README.md
```

## Core behavior

- Declarative figure specs with figure title, figure subtitle, panel order, tile metadata, chart bindings, and render policies.
- Multipanel layouts with presets plus custom grids.
- Broad chart coverage across univariate, bivariate, multivariate, compositional, and diagnostic plot families.
- ColorBrewer-backed palette resolution with deterministic mutation metadata.
- Discovery tooling for large local trees such as `/Users/renatosocodato`.
- Manifest generation with checksums, output contracts, timestamps, and spec signatures.
- Legacy adapters for older 4-panel and supplementary workflows.

## Composition grid

Panel counts map to a fixed `(rows × cols)` grid when neither explicit `rows`/`cols` nor a preset is supplied:

| Panels | Grid | Cells | Empty |
|-------:|:----:|:-----:|:-----:|
| 4      | 2×2  | 4     | 0     |
| 5      | 3×2  | 6     | 1     |
| 6      | 3×3  | 9     | 3     |
| 7      | 4×3  | 12    | 5     |
| 9      | 3×3  | 9     | 0     |

Counts 1–3 remain single-column; other counts fall back to the square-ish ceiling layout. Explicit `layout.rows`/`layout.cols` or a preset always override the table above.

## Output contract

The default output policy is fixed and publication-friendly:

- Every render pass emits a **vector PDF** *and* a **high-resolution PNG** for every panel and for the assembled figure — on the same pass.
- PDF (and SVG) are true vector output with embedded Type 42 fonts and a `Creator` metadata tag.
- PNG/TIFF/JPEG are rasterized at `max(spec_dpi, 600)` so the raster artifact is always publication-ready; PNG is written with `optimize=True`.
- Additional formats (`svg`, `tiff`, `jpg`) can be requested explicitly without replacing `pdf` and `png`.

## Commands you will actually use

```bash
make bootstrap
make inspect
make discover
make render-single
make render-four
make smoke
make clean
```

Direct CLI equivalents:

```bash
panelforge inspect examples/specs/four_panel.yaml
panelforge render examples/specs/single_panel.yaml --out outputs/single
panelforge discover --roots /Users/renatosocodato --output outputs/discovery.json
panelforge tile examples/specs/four_panel.yaml --output outputs/tile.json
```

## Minimal spec

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
        path: "examples/data/multimodal_demo.csv"
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

## Style contract

- Helvetica-first rendering (Helvetica → Helvetica Neue → Arial → Liberation Sans → sans) with embedded Type 42 fonts in PDF/PS and untouched SVG text for downstream editability.
- Large bold panel labels (`A`, `B`, `C`…) anchored outside each axes top-left.
- Panel titles are hard-capped at three words on a single line; longer titles are truncated via `panelforge.style.short_title`.
- No footers. No figure caption, no panel-level meta line, no outcome pill — nothing is rendered below the data. Metadata lives in the manifest, not on the canvas.
- Grid-free axes, thin grey spines on left and bottom only.
- `panelforge.style` exports the reusable primitives: `panel_label`, `tile_axes`, `annotation_note`, `row_separator`, `short_title`.
- The visual baseline stays minimal and restrained so panels can mix across analysis domains without looking incoherent.

## Python and R parity

Python and R both render from the same YAML structure.

- Python path: `panelforge render ...`
- R path: `Rscript R/panel_renderer.R examples/specs/single_panel.yaml outputs/r-run`

The R renderer walks the same sans-serif stack (Helvetica → Helvetica Neue → Arial → Liberation Sans) and degrades safely to `sans` when none is installed.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). If you add a chart family, adapter, or manifest field, update `examples/specs/` and `tests/` in the same change so the repo stays clone-safe for the next user.

## Current release

The repository is published and currently aligned to `v0.1.4`.
