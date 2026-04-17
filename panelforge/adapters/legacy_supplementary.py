from __future__ import annotations

from pathlib import Path
from typing import List

from ..schema import FigureSpec, DataSourceSpec, ChartSpec, MappingSpec, PanelSpec, PanelTileSpec, PaletteSpec


def build_legacy_supplementary_spec(paper_root: str, phase: int, panel_label: str) -> FigureSpec:
    root = Path(paper_root)
    analysis_dir = root / "data_bundle" / f"analysis_{phase:02d}"
    files = sorted(analysis_dir.glob("*.csv"))
    if not files:
        files = sorted(analysis_dir.glob("*"))

    panels: List[PanelSpec] = []
    for idx, file in enumerate(files[:4]):
        path = str(file)
        panels.append(
            PanelSpec(
                label=chr(ord("S") + idx),
                title=f"Supplementary {phase:02d}-{idx + 1}: {file.name}",
                subtitle="Supplementary compatibility path",
                tile=PanelTileSpec(label=chr(ord("S") + idx), title="supp", subtitle="legacy", status="pass"),
                chart=ChartSpec(
                    chart_type="hist" if file.suffix.lower() in {".csv", ".tsv"} else "box",
                    data=DataSourceSpec(path=path, format="auto"),
                    mappings=MappingSpec(),
                    options={},
                ),
                output_name=f"analysis_{phase:02d}_supplementary_{chr(ord('S') + idx)}",
            )
        )

    if not panels:
        fallback = analysis_dir / "placeholder.txt"
        panels.append(
            PanelSpec(
                label=panel_label,
                title=f"Supplementary {phase:02d}: fallback",
                subtitle="No files detected",
                tile=PanelTileSpec(label=panel_label, title="supp", subtitle="fallback", status="warn"),
                chart=ChartSpec(chart_type="bar", data=DataSourceSpec(path=str(fallback), format="csv"), mappings=MappingSpec(x="value", y="value")),
                output_name=f"analysis_{phase:02d}_supplementary_{panel_label}",
            )
        )

    return FigureSpec(
        title=f"Legacy Supplementary Phase {phase:02d}",
        subtitle="Distinct supplementary compatibility rendering",
        layout={"rows": 2, "cols": 2},
        panels=panels,
        prefix=f"analysis_{phase:02d}_supplementary",
        palette=PaletteSpec(role="annotation", palette="Set1", family="qualitative"),
    )

