import json
from pathlib import Path

import pytest

from panelforge.render import render_spec
from panelforge.render.engine import _layout_from_spec


def test_render_contract_pdf_and_png_exist(tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    spec = repo_root / "examples" / "specs" / "single_panel.yaml"
    output = render_spec(spec, output_dir=tmp_path / "single", write_manifest=True)

    panels = output["panels"]
    assert len(panels) == 1
    files = panels[0]["files"]
    assert Path(files["pdf"]).exists()
    assert Path(files["png"]).exists()
    assert panels[0]["checksums"]["pdf"] == __import__("hashlib").sha256(Path(files["pdf"]).read_bytes()).hexdigest()

    assembled = output["assembled"]
    assert Path(assembled["files"]["pdf"]).exists()
    assert Path(assembled["files"]["png"]).exists()


def test_render_generates_manifest_with_checksum_payload(tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    spec = repo_root / "examples" / "specs" / "four_panel.yaml"
    output = render_spec(spec, output_dir=tmp_path / "four", write_manifest=True)
    manifest_path = Path(output["manifest"])
    assert manifest_path.exists()

    payload = json.loads(manifest_path.read_text())
    assert payload["schema_version"] == "1.0.0"
    assert payload["command"] == "panelforge render"
    assert len(payload["panels"]) == 4
    assert len(payload["figures"]) == 1
    assert all("checksum" in item for item in payload["panels"])
    assert all(Path(item["file"]).exists() for item in payload["panels"])


@pytest.mark.parametrize(
    "count,expected",
    [
        (4, (2, 2)),
        (5, (3, 2)),
        (6, (3, 3)),
        (7, (4, 3)),
        (9, (3, 3)),
    ],
)
def test_layout_from_spec_honours_mandated_grids(count: int, expected: tuple[int, int]) -> None:
    assert _layout_from_spec(count, preset=None, rows=None, cols=None) == expected


def test_render_emits_vector_pdf_and_highres_png_per_pass(tmp_path) -> None:
    """Every render pass must ship a vector PDF and a high-res PNG for every artifact."""

    repo_root = Path(__file__).resolve().parents[1]
    spec = repo_root / "examples" / "specs" / "four_panel.yaml"
    output = render_spec(spec, output_dir=tmp_path / "dual", write_manifest=False)

    artifacts = [panel["files"] for panel in output["panels"]]
    artifacts.append(output["assembled"]["files"])

    for files in artifacts:
        pdf_path = Path(files["pdf"])
        png_path = Path(files["png"])
        assert pdf_path.exists() and png_path.exists()
        assert pdf_path.read_bytes().startswith(b"%PDF-"), f"{pdf_path} is not a vector PDF"
        assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), f"{png_path} is not a PNG"
