"""Contracts — malformed input raises, valid input round-trips."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from figures.core.contract import (
    CoefForestInput,
    DistributionByGroupInput,
    SobolInput,
    VolcanoInput,
)


def test_sobol_accepts_numpy_and_casts_to_float() -> None:
    c = SobolInput(parameters=["a"], S1=[0.5], S1_ci=[0.05])
    assert isinstance(c.S1, np.ndarray)
    assert c.S1.dtype == float


def test_volcano_requires_dataframe() -> None:
    with pytest.raises(ValidationError):
        VolcanoInput(df="not a dataframe")


def test_coef_forest_arrays_round_trip() -> None:
    c = CoefForestInput(terms=["a", "b"], estimate=[0.1, 0.2],
                        ci_lo=[0.0, 0.1], ci_hi=[0.2, 0.3])
    assert list(c.terms) == ["a", "b"]


def test_distribution_input_literal_overlay_enforced() -> None:
    df = pd.DataFrame({"v": [1, 2], "g": ["a", "b"]})
    with pytest.raises(ValidationError):
        DistributionByGroupInput(df=df, value_col="v", group_col="g",
                                 overlay="not_a_valid_mode")
