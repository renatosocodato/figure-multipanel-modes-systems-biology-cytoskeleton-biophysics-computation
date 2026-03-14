import json
from pathlib import Path

import yaml

from panelforge.schema import FigureSpec


ROOT = Path(__file__).resolve().parents[1]


def test_figure_spec_loads_required_fields() -> None:
    spec_path = ROOT / "examples" / "specs" / "single_panel.yaml"
    payload = yaml.safe_load(spec_path.read_text())
    spec = FigureSpec(**payload)
    assert spec.title == "Single panel demo"
    assert spec.subtitle == "Panel-level pipeline smoke and Arial tile checks"
    assert len(spec.panels) == 1
    assert spec.panels[0].chart.type in {"hist", "histogram"}
    assert spec.panels[0].tile.label == "A"


def test_figure_spec_to_json_round_trip() -> None:
    payload = {
        "title": "JSON roundtrip",
        "subtitle": "Smoke spec",
        "layout": {"rows": 1, "cols": 1},
        "panels": [
            {
                "label": "A",
                "title": "Panel",
                "subtitle": "Panel subtitle",
                "chart": {
                    "chart_type": "dot",
                    "data": {"path": "examples/data/multimodal_demo.csv", "format": "csv"},
                    "mappings": {"x": "x", "y": "y"},
                },
            }
        ],
    }
    spec = FigureSpec(**payload)
    dumped = spec.model_dump()
    reloaded = FigureSpec(**json.loads(json.dumps(dumped)))
    assert reloaded.title == spec.title
    assert reloaded.panels[0].tile.outcome == "pass"
