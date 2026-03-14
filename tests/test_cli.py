from pathlib import Path

from panelforge.discovery.scanner import phase_discovery


def test_discover_runs_without_root_errors() -> None:
    hits = phase_discovery(roots=["/does/not/exist", "/nonexistent"], include=["analysis_*"], exclude=[".git"])
    assert hits == {}


def test_discovery_includes_analysis_like_roots(tmp_path) -> None:
    root = tmp_path / "project"
    (root / "analysis_alpha").mkdir(parents=True)
    (root / "analysis_alpha" / "panel.csv").write_text("x,y\n1,2\n")
    found = phase_discovery(roots=[str(root)], include=["analysis_*"], exclude=[".git"])
    assert "analysis_alpha" in found
    assert any(str(root / "analysis_alpha") == item for item in found["analysis_alpha"])
