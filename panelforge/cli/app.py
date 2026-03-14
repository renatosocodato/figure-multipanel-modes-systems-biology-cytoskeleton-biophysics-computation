from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
import json
from typing import Any

import yaml

from ..discovery import phase_discovery
from ..manifests.core import ManifestBuilder, save_manifest
from ..render import inspect_spec as inspect_spec_impl
from ..render import render_spec
from ..schema import FigureSpec, SCHEMA_VERSION
from ..adapters import build_legacy_main_4panel_spec, build_legacy_supplementary_spec


def _load_spec(spec_path: Path) -> dict[str, Any]:
    with Path(spec_path).open() as handle:
        if spec_path.suffix.lower() == ".json":
            payload = json.load(handle)
        else:
            payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise TypeError(f"Spec payload must be a mapping, got {type(payload)}")
    return payload


def _emit(payload: dict[str, Any], output: str | None) -> int:
    if output:
        Path(output).write_text(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
    return 0


def _cmd_discover(args: Namespace) -> int:
    roots = [r for r in args.roots.split(",") if r]
    if not roots:
        roots = ["/Users/renatosocodato"]
    include = [p for p in args.include.split(",") if p] if args.include else ["analysis_*"]
    exclude = [p for p in args.exclude.split(",") if p] if args.exclude else [".git", ".venv", "__pycache__", "tmp"]
    discovered = phase_discovery(roots=roots, include=include, exclude=exclude)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "roots": discovered,
        "roots_count": len(discovered),
        "roots_list": sorted(discovered.keys()),
    }
    return _emit(payload, args.output)


def _cmd_inspect(args: Namespace) -> int:
    diagnostics = inspect_spec_impl(Path(args.spec))
    return _emit(diagnostics, args.output)


def _cmd_render(args: Namespace) -> int:
    output = render_spec(Path(args.spec), output_dir=Path(args.out) if args.out else None, write_manifest=not args.no_manifest)
    payload = {
        "figure": output.get("figure"),
        "panels": output.get("panels", []),
        "formats": output.get("formats", ["pdf", "png"]),
        "manifest": output.get("manifest"),
        "command": "panelforge render",
        "timestamp": output.get("timestamp"),
        "spec_signature": output.get("spec_signature"),
    }
    return _emit(payload, args.output)


def _cmd_render_legacy_main(args: Namespace) -> int:
    if args.phase < 1:
        raise SystemExit("phase must be >= 1")
    spec = build_legacy_main_4panel_spec(args.paper_root, args.phase)
    output_path = Path(args.paper_root) / ".panelforge-legacy-main.yaml" if args.temp_spec == ".panelforge-legacy-main.yaml" else Path(args.temp_spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        yaml.safe_dump(spec.model_dump(), handle)
    output = render_spec(output_path, output_dir=Path(args.out) if args.out else None, write_manifest=not args.no_manifest)
    return _emit(output, args.output)


def _cmd_render_legacy_supplementary(args: Namespace) -> int:
    if args.phase < 1:
        raise SystemExit("phase must be >= 1")
    spec = build_legacy_supplementary_spec(args.paper_root, args.phase, args.panel_label)
    output_path = Path(args.paper_root) / ".panelforge-legacy-supplementary.yaml" if args.temp_spec == ".panelforge-legacy-supplementary.yaml" else Path(args.temp_spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        yaml.safe_dump(spec.model_dump(), handle)
    output = render_spec(output_path, output_dir=Path(args.out) if args.out else None, write_manifest=not args.no_manifest)
    return _emit(output, args.output)


def _cmd_manifest(args: Namespace) -> int:
    payload = _load_spec(Path(args.render_output))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(payload, dict) and {"command", "schema_version", "figure", "panels"} <= payload.keys() and isinstance(payload.get("panels"), list):
        out.write_text(json.dumps(payload, indent=2))
        return 0

    if not isinstance(payload, dict) or "figure" not in payload:
        return 1

    mb = ManifestBuilder(
        command="panelforge manifest",
        figure=payload.get("figure", {}),
        palette=payload.get("palette", {}),
    )
    for p in payload.get("panels", []):
        if not isinstance(p, dict):
            continue
        status = p.get("status", "ok")
        width = float(p.get("width_in", payload.get("figure", {}).get("render", {}).get("width", 8.0)))
        height = float(p.get("height_in", payload.get("figure", {}).get("render", {}).get("height", 6.0)))
        file_map = p.get("files", {})
        file_candidates = list(file_map.values()) if isinstance(file_map, dict) else []
        if file_candidates:
            mb.add_panel(p.get("label", p.get("panel", "panel")), status, Path(file_candidates[0]), width, height)
    save_manifest(mb, out)
    return 0


def _cmd_tile(args: Namespace) -> int:
    spec = FigureSpec(**_load_spec(Path(args.spec)))
    payload = {
        "status": "ok",
        "figure_title": spec.title,
        "figure_subtitle": spec.subtitle,
        "panel_count": len(spec.panels),
        "tiles": [
            {
                "panel": panel.label,
                "panel_title": panel.title,
                "panel_subtitle": panel.subtitle,
                "tile_label": panel.tile.label,
                "tile_title": panel.tile.title,
                "tile_subtitle": panel.tile.subtitle,
                "tile_status": panel.tile.status,
                "outcome": panel.tile.outcome,
            }
            for panel in spec.panels
        ],
        "palette": spec.palette.model_dump() if spec.palette else None,
    }
    return _emit(payload, args.output)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="panelforge", description="Universal multipanel figure factory")
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="discover analysis roots")
    discover.add_argument("--roots", default="/Users/renatosocodato")
    discover.add_argument("--include", default="analysis_*")
    discover.add_argument("--exclude", default=".git,.venv,__pycache__,tmp")
    discover.add_argument("--output", default=None)
    discover.set_defaults(func=_cmd_discover)

    inspect = sub.add_parser("inspect", help="inspect figure spec and mapping diagnostics")
    inspect.add_argument("spec")
    inspect.add_argument("--output", default=None)
    inspect.set_defaults(func=_cmd_inspect)

    render_cmd = sub.add_parser("render", help="render a figure spec")
    render_cmd.add_argument("spec")
    render_cmd.add_argument("--out", default=None)
    render_cmd.add_argument("--output", default=None)
    render_cmd.add_argument("--no-manifest", action="store_true")
    render_cmd.set_defaults(func=_cmd_render)

    legacy_main = sub.add_parser("render-legacy-main", help="render legacy main 4-panel workflow")
    legacy_main.add_argument("--paper-root", required=True)
    legacy_main.add_argument("--phase", type=int, required=True)
    legacy_main.add_argument("--out", default=None)
    legacy_main.add_argument("--output", default=None)
    legacy_main.add_argument("--temp-spec", default=".panelforge-legacy-main.yaml")
    legacy_main.add_argument("--no-manifest", action="store_true")
    legacy_main.set_defaults(func=_cmd_render_legacy_main)

    legacy_supp = sub.add_parser("render-legacy-supplementary", help="render legacy supplementary workflow")
    legacy_supp.add_argument("--paper-root", required=True)
    legacy_supp.add_argument("--phase", type=int, required=True)
    legacy_supp.add_argument("--panel-label", default="S1")
    legacy_supp.add_argument("--out", default=None)
    legacy_supp.add_argument("--output", default=None)
    legacy_supp.add_argument("--temp-spec", default=".panelforge-legacy-supp.yaml")
    legacy_supp.add_argument("--no-manifest", action="store_true")
    legacy_supp.set_defaults(func=_cmd_render_legacy_supplementary)

    manifest = sub.add_parser("manifest", help="build manifest from render output JSON")
    manifest.add_argument("render_output")
    manifest.add_argument("--output", default="run_manifest.json")
    manifest.set_defaults(func=_cmd_manifest)

    tile = sub.add_parser("tile", help="export panel tile metadata")
    tile.add_argument("spec")
    tile.add_argument("--output", default=None)
    tile.set_defaults(func=_cmd_tile)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
