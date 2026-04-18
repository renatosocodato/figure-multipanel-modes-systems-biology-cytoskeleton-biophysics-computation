"""apply_style() is idempotent and writes the expected rcParams."""
from __future__ import annotations

import matplotlib.pyplot as plt

from figures.core.style import BASE_RCPARAMS, apply_style


def _eq(expected, actual) -> bool:
    # matplotlib coerces single-string keys like font.family into lists.
    if isinstance(actual, list) and not isinstance(expected, list):
        return [expected] == actual
    return expected == actual


def test_apply_style_writes_baseline_rcparams() -> None:
    apply_style()
    for key, value in BASE_RCPARAMS.items():
        assert _eq(value, plt.rcParams[key]), f"{key}: expected {value!r} got {plt.rcParams[key]!r}"


def test_apply_style_is_idempotent() -> None:
    apply_style()
    before = {k: plt.rcParams[k] for k in BASE_RCPARAMS}
    apply_style()
    apply_style()
    after = {k: plt.rcParams[k] for k in BASE_RCPARAMS}
    assert before == after


def test_apply_style_default_alias_accepted() -> None:
    apply_style("default")
    assert plt.rcParams["axes.titleweight"] == "bold"
