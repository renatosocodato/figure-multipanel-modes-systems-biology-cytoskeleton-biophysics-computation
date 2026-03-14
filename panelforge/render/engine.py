from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from ..palette import resolve_palette
from ..schema import FigureSpec, PaletteSpec
from ..charts.base import RenderContext
from ..charts.registry import registry
from ..manifests.core import ManifestBuilder, save_manifest
from ..style.theme import enforce_minimal_theme, tile_axes
from ..transforms.core import apply_transforms, infer_missing_columns, suggest_mappings


def _serialize_diagnostics(entries: Iterable[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for entry in entries:
        if isinstance(entry, dict):
            out.append(dict(entry))
            continue
        if isinstance(entry, tuple) and len(entry) == 2:
            out.append({"message": str(entry[0]), "details": entry[1]})
            continue
        if hasattr(entry, "message"):
            payload = {"message": str(getattr(entry, "message"))}
            if hasattr(entry, "details"):
                payload["details"] = getattr(entry, "details")
            out.append(payload)
            continue
        out.append({"message": str(entry)})
    return out


def _save_figure(fig: plt.Figure, target: Path, dpi: int) -> None:
    suffix = target.suffix.lower().lstrip(".")
    if suffix in {"pdf", "svg"}:
        fig.savefig(target, bbox_inches="tight")
        return

    save_kwargs = {"bbox_inches": "tight", "dpi": dpi}
    if suffix in {"tiff", "jpg", "jpeg", "png"}:
        format_name = "jpeg" if suffix == "jpg" else suffix
        fig.savefig(target, format=format_name, **save_kwargs)
        return

    fig.savefig(target, format="png", **save_kwargs)


def _safe_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(value)) or "panel"


def _checksum_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_figure(spec_path: Path) -> FigureSpec:
    with spec_path.open() as handle:
        raw = yaml.safe_load(handle) if spec_path.suffix.lower() in {".yaml", ".yml"} else json.load(handle)
    if not isinstance(raw, dict):
        raise TypeError(f"Spec payload must be mapping; got {type(raw)}")
    spec = FigureSpec(**raw)
    spec_dir = spec_path.parent
    for panel in spec.panels:
        panel.chart.data.path = _resolve_data_path(panel.chart.data.path, spec_dir)
    return spec


def _resolve_data_path(raw_path: str, spec_dir: Path) -> str:
    path_obj = Path(raw_path)
    if path_obj.is_absolute():
        return raw_path
    candidate = (spec_dir / path_obj).resolve()
    return str(candidate if candidate.exists() else path_obj)


def _normalise_formats(formats: Iterable[str]) -> List[str]:
    requested = []
    for value in formats:
        token = str(value).lower()
        if token in {"pdf", "png", "svg", "tiff", "jpg"} and token not in requested:
            requested.append(token)
    for token in ("pdf", "png"):
        if token not in requested:
            requested.insert(0, token)
    return requested


def _layout_from_spec(count: int, preset: Optional[str], rows: Optional[int], cols: Optional[int]) -> Tuple[int, int]:
    if rows and cols:
        return max(1, int(rows)), max(1, int(cols))
    if preset:
        p = preset.upper()
        if p == "A":
            return 1, 1
        if p == "B":
            return 1, 2
        if p == "C":
            return 2, 2
        if p == "D":
            return 2, 3
    if count <= 1:
        return 1, 1
    if count == 2:
        return 1, 2
    if count == 3:
        return 1, 3
    col_count = min(4, count)
    row_count = math.ceil(count / col_count)
    return row_count, col_count


def _required_columns_for_chart(chart_type: str) -> List[str]:
    required = {
        "bar": ["x", "y"],
        "lollipop": ["x", "y"],
        "hist": ["x"],
        "histogram": ["x"],
        "kde": ["x"],
        "ecdf": ["x"],
        "box": ["x", "y"],
        "violin": ["x", "y"],
        "dot": ["x", "y"],
        "dot_plot": ["x", "y"],
        "scatter": ["x", "y"],
        "line": ["x", "y"],
        "area": ["x", "y"],
        "stacked_area": ["x", "y"],
        "regression": ["x", "y"],
        "regression_ci": ["x", "y"],
        "hexbin": ["x", "y"],
        "correlogram": [],
        "heatmap": [],
        "cluster_heatmap": [],
        "corr_matrix": [],
        "pca": ["x", "y"],
        "pca_scatter": ["x", "y"],
        "tsne": ["x", "y"],
        "tsne_scatter": ["x", "y"],
        "umap": ["x", "y"],
        "umap_scatter": ["x", "y"],
        "stacked_bar": ["category", "y"],
        "stacked_bar_100": ["category", "y"],
        "outcome_composition": ["category"],
        "tally_tiles": ["category"],
        "roc": ["y", "group"],
        "pr": ["y", "group"],
        "precision_recall": ["y", "group"],
        "calibration": ["y", "group"],
        "residuals": ["x", "y"],
        "qq": ["x"],
        "ma": ["x", "y"],
        "volcano": ["x", "y"],
        "manhattan": ["x", "y"],
    }
    return required.get(chart_type, ["x", "y"])


def _read_data(path: str, fmt: str) -> pd.DataFrame:
    return _read_data_with_base(path, fmt, spec_dir=None)


def _read_data_with_base(path: str, fmt: str, spec_dir: Optional[Path]) -> pd.DataFrame:
    path_obj = Path(path)
    if not path_obj.is_absolute() and spec_dir is not None:
        candidate = (spec_dir / path_obj).resolve()
        if candidate.exists():
            path_obj = candidate
    if not path_obj.exists():
        return pd.DataFrame({"fallback": [0.0, 1.0, 2.0], "value": [1, 2, 3]})
    resolved = (fmt or "auto").lower()
    if resolved in {"", "auto"}:
        resolved = path_obj.suffix.lower().lstrip(".")
    if resolved in {"tsv", "tab"}:
        return pd.read_csv(path_obj, sep="\t")
    if resolved == "feather":
        return pd.read_feather(path_obj)
    if resolved == "parquet":
        return pd.read_parquet(path_obj)
    if resolved == "json":
        return pd.read_json(path_obj)
    if resolved == "npy":
        return pd.DataFrame(np.load(path_obj))
    return pd.read_csv(path_obj)


def _normalise_chart_type(chart_type: str) -> str:
    return {
        "histogram": "hist",
        "boxplot": "box",
        "qq_plot": "qq",
        "precision-recall": "precision_recall",
    }.get(chart_type.lower().replace("-", "_"), chart_type.lower().replace("-", "_"))


def _infer_mappings(chart_panel, data: pd.DataFrame) -> Tuple[dict[str, Any], List[dict[str, str]]]:
    chart_type = _normalise_chart_type(getattr(chart_panel.chart, "chart_type", chart_panel.chart.type))
    required = _required_columns_for_chart(chart_type)
    mappings = chart_panel.chart.mappings.model_dump()
    suggestions = suggest_mappings(data)

    inferred: List[dict[str, str]] = []
    missing = [key for key in required if not mappings.get(key)]
    for key in missing:
        suggestion = suggestions.get(key)
        if suggestion and suggestion in data.columns:
            mappings[key] = suggestion
            inferred.append({"field": key, "source": "inferred", "value": suggestion})
        elif data.columns.size > 0:
            fallback_key = data.columns[0]
            if key in {"x", "category"}:
                mappings["x"] = fallback_key
            elif key == "y" and data.columns.size > 1:
                mappings["y"] = data.columns[1]
            elif key not in mappings:
                mappings[key] = data.columns[0]
            inferred.append({"field": key, "source": "fallback", "value": mappings[key]})

    return mappings, inferred


def inspect_spec(spec_path: str | Path) -> dict[str, Any]:
    spec = _load_figure(Path(spec_path))
    spec_dir = Path(spec_path).parent
    panel_diagnostics: List[dict[str, Any]] = []

    for panel in spec.panels:
        data = _read_data_with_base(panel.chart.data.path, panel.chart.data.format, spec_dir)
        mappings = panel.chart.mappings.model_dump()
        chart_type = _normalise_chart_type(getattr(panel.chart, "chart_type", panel.chart.type))
        required = _required_columns_for_chart(chart_type)
        missing, suggestions = infer_missing_columns(data, required)
        panel_diagnostics.append(
            {
                "panel": panel.label,
                "chart": chart_type,
                "rows": int(data.shape[0]),
                "columns": [str(c) for c in data.columns],
                "mapping_count": len(mappings),
                "required": required,
                "missing": missing,
                "suggestions": suggestions,
                "mappings": mappings,
                "transforms": len(panel.transforms),
            }
        )

    return {
        "schema_version": spec.schema_version,
        "figure_title": spec.title,
        "figure_subtitle": spec.subtitle,
        "layout": spec.layout.model_dump(),
        "panel_count": len(spec.panels),
        "panels": panel_diagnostics,
    }


def _render_single_panel(panel, render_conf, palette_info: Dict[str, Any], spec_dir: Optional[Path] = None) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    raw = _read_data_with_base(panel.chart.data.path, panel.chart.data.format, spec_dir)
    transformed, warnings = apply_transforms(raw.copy(), [t.model_dump() for t in panel.transforms])
    data = transformed
    mappings, inferred = _infer_mappings(panel, data)
    diagnostics: List[Any] = []
    diagnostics.extend(_serialize_diagnostics(warnings))
    diagnostics.extend(inferred)

    chart_type = _normalise_chart_type(getattr(panel.chart, "chart_type", panel.chart.type))
    payload = panel.chart.model_dump()
    payload["mappings"] = mappings

    try:
        renderer = registry.resolve(chart_type)
    except KeyError:
        inferred.append({"field": "chart_type", "source": "fallback", "value": "bar"})
        chart_type = "bar"
        renderer = registry.resolve(chart_type)
        diagnostics.append(
            {
                "message": "Unknown chart type, falling back to bar",
                "details": {"chart_type": getattr(panel.chart, "chart_type", panel.chart.type)},
            }
        )

    ctx = RenderContext(
        data=data,
        chart_spec=payload,
        palette=palette_info["colors"],
        width=float(render_conf.width),
        height=float(render_conf.height),
    )
    fig, ax = renderer(ctx, chart_type, panel=panel)
    enforce_minimal_theme(ax)
    tile_axes(ax, panel.tile.label, panel.tile.title, panel.tile.subtitle, panel.tile.status)
    if panel.tile.outcome and str(panel.tile.outcome).lower() not in {"", "none", "na"}:
        ax.text(
            0.98,
            0.02,
            str(panel.tile.outcome).upper(),
            transform=ax.transAxes,
            fontsize=7,
            ha="right",
            va="bottom",
            bbox={"boxstyle": "round,pad=0.1", "facecolor": "#ecfdf3", "edgecolor": "#16a34a"},
        )
    fig.tight_layout()
    status = "warn" if diagnostics else "ok"
    return {
        "figure": fig,
        "ax": ax,
        "chart_type": chart_type,
        "palette": {"id": palette_info["palette_id"], "hash": palette_info["palette_hash"]},
        "mappings": mappings,
        "diagnostics": diagnostics,
        "status": status,
    }, diagnostics


def render_panel(panel, output_dir: Path, render_conf, palette_info: Dict[str, Any], formats: Optional[Iterable[str]] = None, spec_dir: Optional[Path] = None) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_formats = _normalise_formats(formats or render_conf.formats)
    rendered, diagnostics = _render_single_panel(panel, render_conf, palette_info, spec_dir=spec_dir)
    fig = rendered["figure"]
    base = _safe_filename(panel.output_name or panel.label)
    file_map: Dict[str, str] = {}

    for fmt in resolved_formats:
        target = output_dir / f"{base}.{fmt}"
        _save_figure(fig, target, dpi=int(render_conf.dpi or 600))
        file_map[fmt] = str(target)

    plt.close(fig)
    checksums = {fmt: _checksum_file(Path(path)) for fmt, path in file_map.items()}

    return {
        "label": panel.label,
        "title": panel.title,
        "subtitle": panel.subtitle,
        "files": file_map,
        "checksums": checksums,
        "diagnostics": diagnostics,
        "width_in": float(render_conf.width),
        "height_in": float(render_conf.height),
        "palette": rendered["palette"],
        "mappings": rendered["mappings"],
        "status": rendered["status"],
    }


def assemble_figure(spec: FigureSpec, panels: List[Dict[str, Any]], output_dir: Path, formats: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_formats = _normalise_formats(formats or spec.render.formats)
    render_rows, render_cols = _layout_from_spec(len(panels), spec.layout.preset, spec.layout.rows, spec.layout.cols)
    fig, axes = plt.subplots(render_rows, render_cols, figsize=(spec.render.width * render_cols, spec.render.height * render_rows))
    axes = np.array(axes).reshape(-1)
    fig.suptitle(spec.title)

    for axis in axes:
        axis.set_axis_off()

    for idx, panel in enumerate(panels):
        path = panel.get("files", {}).get("png", "")
        png = Path(path)
        if not path or not png.exists() or idx >= len(axes):
            continue
        axis = axes[idx]
        axis.set_axis_off()
        axis.set_title(panel.get("label", ""))
        axis.imshow(mpimg.imread(png))

    plt.tight_layout()
    enforce_minimal_theme()

    out_files: Dict[str, str] = {}
    for fmt in resolved_formats:
        target = output_dir / f"{spec.prefix}.{fmt}"
        _save_figure(fig, target, dpi=int(spec.render.dpi or 600))
        out_files[fmt] = str(target)
    plt.close(fig)

    return {
        "files": out_files,
        "layout": {"rows": render_rows, "cols": render_cols},
        "checksum": {fmt: _checksum_file(Path(path)) for fmt, path in out_files.items()},
        "dimensions": {
            "width_in": float(spec.render.width * render_cols),
            "height_in": float(spec.render.height * render_rows),
        },
    }


def render_spec(spec_path: str | Path, output_dir: Optional[Path] = None, write_manifest: bool = True) -> Dict[str, Any]:
    spec = _load_figure(Path(spec_path))
    out_dir = Path(output_dir) if output_dir else Path(spec_path).parent / spec.prefix
    out_dir.mkdir(parents=True, exist_ok=True)

    resolved_formats = _normalise_formats(spec.render.formats)
    figure_palette = resolve_palette(spec.palette or PaletteSpec(), n_colors=max(1, len(spec.panels)))
    spec_signature = hashlib.sha256(json.dumps(spec.model_dump(), sort_keys=True, default=str).encode()).hexdigest()
    panel_outputs: List[Dict[str, Any]] = []
    manifest = ManifestBuilder(
        command="panelforge render",
        figure=spec.model_dump(),
        spec_path=Path(spec_path),
        spec_signature=spec_signature,
        palette=figure_palette,
    )

    for panel in spec.panels:
        panel_palette = resolve_palette(panel.palette, n_colors=max(2, len(spec.panels))) if panel.palette else figure_palette
        output = render_panel(panel, out_dir, spec.render, panel_palette, formats=resolved_formats, spec_dir=Path(spec_path).parent)
        panel_outputs.append(output)
        # Always emit both vector and raster records for manifest parity.
        if output["files"]:
            panel_file = output["files"].get("pdf", output["files"].get("png"))
            if panel_file:
                manifest.add_panel(
                    panel.label,
                    output["status"],
                    Path(panel_file),
                    width_in=float(spec.render.width),
                    height_in=float(spec.render.height),
                )

    assembled = assemble_figure(spec, panel_outputs, out_dir, formats=resolved_formats)
    if assembled["files"]:
        figure_file = assembled["files"].get("pdf", assembled["files"].get("png"))
        if figure_file:
            manifest.add_figure(
                figure_label=spec.prefix,
                status="ok",
                file_path=Path(figure_file),
                width_in=float(assembled["dimensions"]["width_in"]),
                height_in=float(assembled["dimensions"]["height_in"]),
            )

    manifest_path = out_dir / "run_manifest.json"
    if write_manifest:
        save_manifest(manifest, manifest_path)

    return {
        "schema_version": spec.schema_version,
        "figure": spec.model_dump(),
        "panels": panel_outputs,
        "assembled": assembled,
        "manifest": str(manifest_path) if write_manifest else None,
        "spec_signature": spec_signature,
    }


def assemble_from_files(figure: FigureSpec, panel_pngs: List[Path], output_dir: Path) -> Path:
    payload: List[Dict[str, Any]] = [
        {"label": path.stem, "files": {"png": str(path)}} for path in panel_pngs
    ]
    assembled = assemble_figure(figure, payload, output_dir, formats=["pdf", "png"])
    return Path(assembled["files"]["pdf"])
