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

## Output contract

The default output policy is fixed and publication-friendly:

- Every panel emits `*.pdf` and `*.png`
- Every assembled figure emits `*.pdf` and `*.png`
- PNG output defaults to high resolution
- Additional formats such as `svg` can be requested explicitly without replacing `pdf` and `png`

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

- Arial-first rendering is enforced where the environment supports it.
- Figure and panel subtitles are first-class metadata, not afterthoughts.
- Panel tiles carry label, title, subtitle, status, and outcome cues.
- The visual baseline stays minimal and restrained so panels can mix across analysis domains without looking incoherent.

## Python and R parity

Python and R both render from the same YAML structure.

- Python path: `panelforge render ...`
- R path: `Rscript R/panel_renderer.R examples/specs/single_panel.yaml outputs/r-run`

The R renderer prefers Arial when available and degrades safely to `sans` when it is not installed.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). If you add a chart family, adapter, or manifest field, update `examples/specs/` and `tests/` in the same change so the repo stays clone-safe for the next user.

## Current release

The repository is published and currently aligned to `v0.1.3`.
