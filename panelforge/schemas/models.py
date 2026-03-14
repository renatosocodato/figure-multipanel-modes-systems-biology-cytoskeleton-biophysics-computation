from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field, ValidationInfo, field_validator, model_validator


SCHEMA_VERSION = "1.0.0"


class BaseSchemaModel(BaseModel):
    """Base model that keeps backward compatible unknown fields as warnings."""

    model_config = {
        "extra": "ignore",
        "populate_by_name": True,
    }


class PaletteSpec(BaseSchemaModel):
    source: Literal["colorbrewer", "matplotlib", "custom"] = "colorbrewer"
    family: Literal["qualitative", "sequential", "diverging", "mixed"] = "qualitative"
    palette: str = "Set2"
    role: Literal["primary", "comparison", "annotation", "status"] = "primary"
    mutation_mode: Literal["none", "muted", "contrast_boost", "emphasis", "status_shift"] = "none"
    seed: Optional[int] = None


class DataSourceSpec(BaseSchemaModel):
    path: str
    format: Optional[Literal["csv", "tsv", "parquet", "feather", "npy", "json", "rds", "auto"]] = "auto"
    options: Dict[str, Any] = Field(default_factory=dict)


class MappingSpec(BaseSchemaModel):
    x: Optional[str] = None
    y: Optional[str] = None
    z: Optional[str] = None
    group: Optional[str] = None
    category: Optional[str] = None
    row: Optional[str] = None
    col: Optional[str] = None
    time: Optional[str] = None
    order: Optional[str] = None
    xerr: Optional[str] = None
    yerr: Optional[str] = None
    lower: Optional[str] = None
    upper: Optional[str] = None
    weight: Optional[str] = None
    facets: List[str] = Field(default_factory=list)


class ChartSpec(BaseSchemaModel):
    chart_type: str = Field(
        validation_alias=AliasChoices("type", "chart_type"),
        serialization_alias="chart_type",
    )
    data: DataSourceSpec
    mappings: MappingSpec = Field(default_factory=MappingSpec)
    options: Dict[str, Any] = Field(default_factory=dict)
    stats: Dict[str, Any] = Field(default_factory=dict)

    @property
    def type(self) -> str:
        return self.chart_type

    @type.setter
    def type(self, value: str) -> None:
        self.chart_type = value


class TransformSpec(BaseSchemaModel):
    op: str
    params: Dict[str, Any] = Field(default_factory=dict)


class PanelTileSpec(BaseSchemaModel):
    label: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = ""
    status: Optional[str] = None
    outcome: Optional[Literal["pass", "warn", "fail", "na"]] = "pass"


class PanelSpec(BaseSchemaModel):
    label: str
    title: str
    subtitle: str
    tile: PanelTileSpec = Field(default_factory=PanelTileSpec)
    chart: ChartSpec
    transforms: List[TransformSpec] = Field(default_factory=list)
    width: Optional[float] = None
    height: Optional[float] = None
    palette: Optional[PaletteSpec] = None
    output_name: Optional[str] = None

    @model_validator(mode="after")
    def enforce_subtitle(self):
        values = self
        if not values.subtitle and values.title:
            values.subtitle = f"{values.title} panel"
        if values.tile is None:
            values.tile = PanelTileSpec()
        if not values.tile.label:
            values.tile.label = values.label
        if not values.tile.title:
            values.tile.title = values.title
        return values


class FigureLayoutSpec(BaseSchemaModel):
    rows: Optional[int] = None
    cols: Optional[int] = None
    preset: Optional[Literal["A", "B", "C", "D", "custom"]] = None
    labels: List[str] = Field(default_factory=list)


class RenderSpec(BaseSchemaModel):
    strict: bool = False
    formats: List[Literal["pdf", "png", "svg", "tiff", "jpg"]] = Field(default_factory=lambda: ["pdf", "png"])
    dpi: int = 600
    width: float = 8.0
    height: float = 6.0
    fallback: str = "warn"
    manifest: bool = True
    overwrite: bool = True
    seed: Optional[int] = None


class DiscoverySpec(BaseSchemaModel):
    roots: List[str] = Field(default_factory=list)
    include: List[str] = Field(default_factory=lambda: ["analysis_*", "*analysis*"])
    exclude: List[str] = Field(default_factory=lambda: [".git", ".venv", "__pycache__", "tmp", "data_bundle/.ipynb_checkpoints"])
    phase_mapping: Dict[str, Any] = Field(default_factory=dict)


class FigureSpec(BaseSchemaModel):
    schema_version: str = SCHEMA_VERSION
    title: str
    subtitle: str
    subtitle_policy: Literal["required", "recommended", "optional"] = "required"
    layout: FigureLayoutSpec = Field(default_factory=FigureLayoutSpec)
    panels: List[PanelSpec]
    output_dir: str = "outputs/figure_outputs"
    prefix: str = "figure"
    palette: Optional[PaletteSpec] = None
    render: RenderSpec = Field(default_factory=RenderSpec)


class PanelOutputSpec(BaseSchemaModel):
    panel_label: str
    status: str
    file: str
    width_in: float
    height_in: float
    checksum: str


class FigureOutputSpec(BaseSchemaModel):
    label: str
    status: str
    file: str
    width_in: float
    height_in: float
    checksum: str


class RunManifest(BaseSchemaModel):
    schema_version: str = SCHEMA_VERSION
    command: str
    timestamp: str
    git_sha: Optional[str] = None
    spec_path: Optional[str] = None
    spec_signature: Optional[str] = None
    figure: Dict[str, Any]
    panels: List[PanelOutputSpec]
    figures: List[FigureOutputSpec] = Field(default_factory=list)
    environment: Dict[str, Any] = Field(default_factory=dict)
    palette: Dict[str, Any] = Field(default_factory=dict)
