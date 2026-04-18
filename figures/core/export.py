"""Export — vector PDF + raster PNG on a single pass, plus manifest.

Contract
--------
Every call ships a vector PDF (Type 42 fonts, ``Creator`` metadata) *and*
a raster PNG (``max(spec_dpi, 600)`` with ``pil_kwargs={"optimize": True}``).
SVG and TIFF are available on request. A sidecar ``*.manifest.json`` is
written when ``manifest=True``, capturing script path, git sha, theme,
palette, timestamp, and checksums.

Outputs default to ``figures/outputs/`` — gitignored.

Example
-------
>>> from figures.core.export import export_figure
>>> paths = export_figure(fig, "fig_demo", theme="default", palette="okabe_ito")
>>> sorted(paths)                                              # doctest: +SKIP
['fig_demo.manifest.json', 'fig_demo.pdf', 'fig_demo.png']
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


HIGH_RES_PNG_DPI = 600
DEFAULT_FORMATS: Tuple[str, ...] = ("pdf", "png")
OUTPUTS_DIR = Path(__file__).resolve().parents[1] / "outputs"


def _normalise_formats(formats: Iterable[str]) -> Tuple[str, ...]:
    seen: list[str] = []
    for f in formats:
        k = str(f).lower()
        if k in {"pdf", "png", "svg", "tiff", "jpg"} and k not in seen:
            seen.append(k)
    for k in ("pdf", "png"):
        if k not in seen:
            seen.insert(0, k)
    return tuple(seen)


def _save_one(fig, target: Path, dpi: int) -> None:
    suffix = target.suffix.lower().lstrip(".")
    if suffix in {"pdf", "svg"}:
        fig.savefig(target, bbox_inches="tight",
                    metadata={"Creator": "figures (panelforge parallel)"})
        return
    raster_dpi = max(int(dpi), HIGH_RES_PNG_DPI)
    save_kwargs: Dict[str, Any] = {"bbox_inches": "tight", "dpi": raster_dpi}
    if suffix == "png":
        save_kwargs["pil_kwargs"] = {"optimize": True}
    fmt = "jpeg" if suffix == "jpg" else suffix
    fig.savefig(target, format=fmt, **save_kwargs)


def _checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_sha() -> Optional[str]:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL,
            cwd=str(Path(__file__).resolve().parent),
        ).decode().strip()
        return sha or None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def export_figure(
    fig,
    stem: str,
    *,
    formats: Sequence[str] = DEFAULT_FORMATS,
    dpi: int = HIGH_RES_PNG_DPI,
    output_dir: Optional[Path] = None,
    manifest: bool = True,
    theme: Optional[str] = None,
    palette: Optional[str] = None,
    input_checksums: Optional[Mapping[str, str]] = None,
    script_path: Optional[str] = None,
) -> Dict[str, str]:
    """Write ``fig`` as vector PDF + high-res PNG (plus any extras in ``formats``).

    Returns a mapping ``{ext: path}`` for every written artifact, including
    ``"manifest"`` when ``manifest=True``.
    """

    stem = str(stem).strip() or "figure"
    out_dir = Path(output_dir) if output_dir is not None else OUTPUTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    written: Dict[str, Path] = {}
    for ext in _normalise_formats(formats):
        target = out_dir / f"{stem}.{ext}"
        _save_one(fig, target, dpi=dpi)
        written[ext] = target

    result: Dict[str, str] = {ext: str(path) for ext, path in written.items()}

    if manifest:
        payload = {
            "stem": stem,
            "theme": theme,
            "palette": palette,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "git_sha": _git_sha(),
            "script_path": script_path or os.environ.get("PYTHONSCRIPT"),
            "input_checksums": dict(input_checksums or {}),
            "outputs": {
                ext: {"path": str(path), "sha256": _checksum(path)}
                for ext, path in written.items()
            },
            "figures_package_version": _package_version(),
        }
        manifest_path = out_dir / f"{stem}.manifest.json"
        manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        result["manifest"] = str(manifest_path)
    return result


def _package_version() -> str:
    from .. import __version__
    return __version__
