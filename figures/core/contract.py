"""Data contracts — Pydantic models every recipe consumes.

Contract
--------
Every recipe accepts a :class:`FigureContract` subclass. Recipes invoke
``<Model>.model_validate(contract)`` on entry so callers may pass either
a dict or an already-constructed instance. Contracts accept ``np.ndarray``
and ``pd.DataFrame`` via ``arbitrary_types_allowed = True``.

Example
-------
>>> from figures.core.contract import SobolInput
>>> import numpy as np
>>> c = SobolInput(
...     parameters=["a", "b"],
...     S1=np.array([0.5, 0.2]),
...     S1_ci=np.array([0.05, 0.03]),
... )
>>> c.parameters
['a', 'b']
"""
from __future__ import annotations

from typing import Annotated, Any, Callable, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, BeforeValidator, ConfigDict


def _coerce_ndarray(value: Any) -> Any:
    if value is None or isinstance(value, np.ndarray):
        return value
    return np.asarray(value, dtype=float).ravel()


def _coerce_ndarray_2d(value: Any) -> Any:
    if value is None or isinstance(value, np.ndarray):
        return value
    return np.asarray(value, dtype=float)


#: 1D float ndarray — accepts lists / tuples and coerces to ``np.ndarray``.
NPArray = Annotated[np.ndarray, BeforeValidator(_coerce_ndarray)]
#: Optional 1D ndarray.
NPArrayOpt = Annotated[Optional[np.ndarray], BeforeValidator(_coerce_ndarray)]
#: N-D ndarray without a ``ravel()`` — keeps shape for images, matrices, embeddings.
NPArrayND = Annotated[np.ndarray, BeforeValidator(_coerce_ndarray_2d)]
NPArrayNDOpt = Annotated[Optional[np.ndarray], BeforeValidator(_coerce_ndarray_2d)]


class FigureContract(BaseModel):
    """Base class for every recipe contract. Allows numpy + pandas payloads."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------


class SobolInput(FigureContract):
    parameters: List[str]
    S1: NPArray
    S1_ci: NPArray
    ST: NPArrayOpt = None
    ST_ci: NPArrayOpt = None
    n_samples: Optional[int] = None


class MorrisInput(FigureContract):
    parameters: List[str]
    mu_star: NPArray
    sigma: NPArray


class RankedContributionInput(FigureContract):
    labels: List[str]
    values: NPArray
    error: NPArrayOpt = None


class ParameterScanInput(FigureContract):
    x: NPArray
    y: NPArray
    gridsize: int = 24
    reference: Optional[float] = None
    annotation: Optional[str] = None


class DimensionlessCollapseInput(FigureContract):
    log_x: NPArray
    log_y: NPArray
    x_label: str = "log Π"
    y_label: str = "log response"


# ---------------------------------------------------------------------------
# Distributions
# ---------------------------------------------------------------------------


class DistributionByGroupInput(FigureContract):
    df: pd.DataFrame
    value_col: str
    group_col: str
    cluster_col: Optional[str] = None
    hue_col: Optional[str] = None
    overlay: Literal["animal_means", "none", "beeswarm"] = "none"


class RidgeInput(FigureContract):
    df: pd.DataFrame
    value_col: str
    group_col: str
    bw_adjust: float = 0.35
    overlap: float = 0.35


class PairedSlopesInput(FigureContract):
    df: pd.DataFrame
    subject_col: str
    condition_col: str
    value_col: str


# ---------------------------------------------------------------------------
# Timecourses
# ---------------------------------------------------------------------------


class TimecourseInput(FigureContract):
    df: pd.DataFrame
    time_col: str = "t"
    value_col: str = "value"
    group_col: Optional[str] = None
    cluster_col: Optional[str] = None
    stim_time: Optional[float] = None


class DoseResponseInput(FigureContract):
    dose: NPArray
    response: NPArray
    response_sem: NPArrayOpt = None
    ec50_guess: float = 1.0


class CalciumRasterInput(FigureContract):
    events: pd.DataFrame  # columns: cell_id, t
    time_col: str = "t"
    cell_col: str = "cell_id"
    bin_size: float = 1.0


class TrajectoryBundleInput(FigureContract):
    t: NPArray
    trajectories: NPArrayND  # shape (n_traj, n_t)


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


class ScatterWithCIInput(FigureContract):
    x: NPArray
    y: NPArray
    xlabel: str = "x"
    ylabel: str = "y"


class BlandAltmanInput(FigureContract):
    a: NPArray
    b: NPArray
    label_a: str = "method A"
    label_b: str = "method B"


class ResidualsInput(FigureContract):
    fitted: NPArray
    residuals: NPArray


class QQInput(FigureContract):
    sample: NPArray


# ---------------------------------------------------------------------------
# Dynamics
# ---------------------------------------------------------------------------


class DynamicsInput(FigureContract):
    U: Optional[Callable[[np.ndarray, str], np.ndarray]] = None
    dU_dx: Optional[Callable[[np.ndarray, str], np.ndarray]] = None
    rhs_2D: Optional[Callable[..., Any]] = None
    conditions: List[str] = ["basal"]
    xlim: Tuple[float, float] = (0.0, 3.0)
    ylim: Tuple[float, float] = (0.0, 3.0)
    grid: int = 24
    fixed_points: Optional[List[Tuple[float, float, str, str]]] = None


class BifurcationInput(FigureContract):
    r: NPArray
    branches: dict  # name -> 1D array over r; NaN marks the gap
    saddle_node: Optional[float] = None


class LimitCycleInput(FigureContract):
    t: NPArray
    xy: NPArrayND  # (n, 2)
    poincare_x: Optional[float] = None


# ---------------------------------------------------------------------------
# Stochastic
# ---------------------------------------------------------------------------


class DwellInput(FigureContract):
    df: pd.DataFrame
    state_col: str = "state"
    log10_dwell_col: str = "log10_dwell_s"


class GillespieInput(FigureContract):
    t: NPArray
    trajectories: NPArrayND  # (n_traj, n_t)
    states: NPArrayNDOpt = None  # shared shaded-region mask


class FPTInput(FigureContract):
    samples: NPArray


class RateScanInput(FigureContract):
    parameter: NPArray
    rate: NPArray
    sem: NPArrayOpt = None
    parameter_label: str = "parameter"
    rate_label: str = "rate"


# ---------------------------------------------------------------------------
# Morphometry
# ---------------------------------------------------------------------------


class ShapeDistributionInput(FigureContract):
    df: pd.DataFrame
    metric_col: str
    group_col: str
    cluster_col: Optional[str] = None


class AiryscanGridInput(FigureContract):
    images: NPArrayND  # (n_thumbs, h, w)
    labels: Optional[List[str]] = None
    scale_length_um: Optional[float] = None


# ---------------------------------------------------------------------------
# Omics
# ---------------------------------------------------------------------------


class VolcanoInput(FigureContract):
    df: pd.DataFrame
    lfc_col: str = "log2FC"
    pval_col: str = "pvalue"
    label_col: Optional[str] = None
    fdr_col: Optional[str] = None
    top_n_labels: int = 10
    lfc_threshold: float = 1.0
    fdr_threshold: float = 0.05


class MAInput(FigureContract):
    df: pd.DataFrame
    m_col: str = "M"
    a_col: str = "A"
    sig_col: Optional[str] = None


class AnnotatedHeatmapInput(FigureContract):
    matrix: NPArrayND
    row_labels: List[str]
    col_labels: List[str]
    row_annotation: Optional[List[str]] = None
    col_annotation: Optional[List[str]] = None
    cmap: str = "RdBu_r"


class GSEABubbleInput(FigureContract):
    df: pd.DataFrame  # columns: pathway, NES, FDR, n_genes
    max_pathways: int = 20


class EnrichmentDotInput(FigureContract):
    df: pd.DataFrame  # columns: ontology, term, ratio, pvalue


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


class UMAPInput(FigureContract):
    embedding: NPArrayND
    metadata: pd.DataFrame
    color_col: Optional[str] = None
    continuous: bool = False
    density_contours: bool = False
    highlight_ids: Optional[List[Any]] = None


class PCABiplotInput(FigureContract):
    scores: NPArrayND  # (n_samples, 2)
    loadings: NPArrayND  # (n_features, 2)
    feature_names: List[str]


class TrajectoryOverlayInput(FigureContract):
    embedding: NPArrayND
    pseudotime: NPArray


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CoefForestInput(FigureContract):
    terms: List[str]
    estimate: NPArray
    ci_lo: NPArray
    ci_hi: NPArray
    highlight: Optional[List[str]] = None
    reference: float = 0.0


class PartialDependenceInput(FigureContract):
    grid: NPArray
    mean: NPArray
    ice: NPArrayNDOpt = None  # (n_instances, n_grid)


class RandomEffectsInput(FigureContract):
    cluster: List[str]
    estimate: NPArray
    se: NPArray


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------


class StackedFractionInput(FigureContract):
    categories: List[str]
    components: List[str]
    matrix: NPArrayND  # (n_cat, n_comp), rows sum to 1 (or 100)


class TernaryInput(FigureContract):
    abc: NPArrayND  # (n, 3), rows sum to 1
    labels: Tuple[str, str, str] = ("A", "B", "C")


class AlluvialInput(FigureContract):
    left_labels: List[str]
    right_labels: List[str]
    flow_matrix: NPArrayND  # (len(left), len(right))


# ---------------------------------------------------------------------------
# Landscape
# ---------------------------------------------------------------------------


class Potential2DInput(FigureContract):
    X: NPArrayND
    Y: NPArrayND
    U: NPArrayND
    vector_field: Optional[Tuple[np.ndarray, np.ndarray]] = None  # (U_grid, V_grid)
    fixed_points: Optional[List[Tuple[float, float, str, str]]] = None


class WaddingtonInput(FigureContract):
    X: NPArrayND
    Y: NPArrayND
    U: NPArrayND
    trajectories: NPArrayNDOpt = None  # (n_traj, n_t, 2)
