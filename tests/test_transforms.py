import pandas as pd

from panelforge.transforms import core as transforms


def test_transform_chain_melt_aggregate_filter() -> None:
    df = pd.DataFrame(
        {
            "group": ["A", "A", "B", "B"],
            "metric": [1.0, 2.0, 3.0, 4.0],
            "value": [10, 20, 30, 40],
        }
    )
    ops = [
        {"op": "melt", "params": {"id_vars": ["group"], "value_vars": ["metric", "value"], "var_name": "measure", "value_name": "measurement"}},
        {"op": "filter", "params": {"expr": ["group != 'A'"]}},
        {"op": "clip", "params": {"column": "measurement", "low": 15, "hi": 50}},
    ]
    output, warnings = transforms.apply_transforms(df, ops)
    assert output is not None
    assert output["group"].nunique() == 1
    assert (output["measurement"] >= 15).all()
    assert warnings == []


def test_transform_unknown_is_reported_and_skipped() -> None:
    df = pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1]})
    output, warnings = transforms.apply_transforms(df, [{"op": "does_not_exist", "params": {}}])
    assert list(output.columns) == ["x", "y"]
    assert len(warnings) == 1
    assert "Unknown transform" in str(warnings[0].message)
