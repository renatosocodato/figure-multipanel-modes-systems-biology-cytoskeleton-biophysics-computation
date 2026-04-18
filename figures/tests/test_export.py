"""Export — vector PDF + raster PNG on one pass, manifest sidecar."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

from figures.core.export import export_figure


def _dummy_fig():
    fig, ax = plt.subplots(figsize=(2.5, 2.0))
    ax.plot([0, 1, 2], [0, 1, 4])
    return fig


def test_export_writes_pdf_and_png(tmp_path) -> None:
    fig = _dummy_fig()
    paths = export_figure(fig, stem="t1", output_dir=tmp_path,
                          theme="default", palette="okabe_ito",
                          manifest=False)
    plt.close(fig)
    pdf = Path(paths["pdf"]); png = Path(paths["png"])
    assert pdf.exists() and png.exists()
    assert pdf.read_bytes().startswith(b"%PDF-")
    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "manifest" not in paths


def test_export_writes_manifest_with_checksums(tmp_path) -> None:
    fig = _dummy_fig()
    paths = export_figure(fig, stem="t2", output_dir=tmp_path,
                          theme="default", palette="okabe_ito",
                          manifest=True, script_path=__file__)
    plt.close(fig)
    manifest = json.loads(Path(paths["manifest"]).read_text())
    assert manifest["stem"] == "t2"
    assert manifest["theme"] == "default"
    assert manifest["palette"] == "okabe_ito"
    for ext in ("pdf", "png"):
        assert manifest["outputs"][ext]["sha256"]


def test_export_accepts_explicit_formats(tmp_path) -> None:
    fig = _dummy_fig()
    paths = export_figure(fig, stem="t3", output_dir=tmp_path,
                          formats=("svg", "png"), manifest=False)
    plt.close(fig)
    # PDF is always present even when not requested.
    assert set(paths).issuperset({"pdf", "png", "svg"})
