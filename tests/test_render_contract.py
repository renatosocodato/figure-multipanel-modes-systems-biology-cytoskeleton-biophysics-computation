import json
from pathlib import Path

from panelforge.render import render_spec


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
