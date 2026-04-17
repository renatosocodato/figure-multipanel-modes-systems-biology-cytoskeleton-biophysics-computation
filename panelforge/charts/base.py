from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class RenderContext:
    data: pd.DataFrame
    chart_spec: Dict[str, Any]
    palette: list[str]
    width: float = 8.0
    height: float = 6.0


class ChartRenderer(Protocol):
    name: str

    def render(self, ctx: RenderContext):
        ...


def _safe_series(data: pd.DataFrame, name: Optional[str], required: bool = True):
    if name is None or name not in data:
        if required:
            raise KeyError(f"Missing required mapping: {name}")
        return pd.Series([np.nan] * len(data))
    return data[name]


def create_panel_axes(width: float, height: float, title: str = "", subtitle: str = ""):
    """Allocate a panel figure + axes. Title/subtitle are ignored; tile_axes owns the title."""

    del title, subtitle
    fig, ax = plt.subplots(figsize=(width, height))
    return fig, ax

