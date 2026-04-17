from __future__ import annotations

from pathlib import Path
from typing import List

from ..schema import FigureSpec, DataSourceSpec, ChartSpec, MappingSpec, PanelSpec, PanelTileSpec, PaletteSpec, RenderSpec


def _panel(path: Path, prefix: str, phase: int, label: str, title: str, chart_type: str, x: str = "x", y: str = "y") -> PanelSpec:
    return PanelSpec(
        label=label,
        title=f"Phase {phase:02d} {title}",
        subtitle="Legacy 4-panel migration path",
        tile=PanelTileSpec(label=label, title=title, subtitle="main workflow", status="pass"),
        chart=ChartSpec(
            chart_type=chart_type,
            data=DataSourceSpec(path=str(path), format="csv"),
            mappings=MappingSpec(x=x, y=y, group="target"),
            options={},
        ),
        output_name=f"analysis_{phase:02d}_main_{label}",
    )


def build_legacy_main_4panel_spec(paper_root: str, phase: int) -> FigureSpec:
    root = Path(paper_root)
    analysis_dir = root / "data_bundle" / f"analysis_{phase:02d}"
    panels: List[PanelSpec] = []

    for idx, (path, chart, title) in enumerate(
        [
            ("compound_rankings.csv", "bar", "Docking inventory by target"),
            ("model_performance.csv", "heatmap", "Model performance matrix"),
            ("state_stratified_de.csv", "scatter", "DE signal scatter"),
            ("causal_priority_table.csv", "box", "Causal scores box"),
        ],
        start=1,
    ):
        candidate = analysis_dir / path
        panels.append(
            _panel(
                candidate,
                "analysis_" + f"{phase:02d}",
                phase,
                chr(ord("A") + idx),
                title,
                chart,
            )
        )

    return FigureSpec(
        title=f"Legacy Phase {phase:02d} Main",
        subtitle="4-panel compatibility rendering",
        layout={"rows": 2, "cols": 2},
        panels=panels,
        prefix=f"analysis_{phase:02d}_main_4panel",
        palette=PaletteSpec(role="primary", palette="Set2", family="qualitative"),
        render=RenderSpec(formats=["pdf", "png"], dpi=600, width=10.0, height=8.0),
    )

