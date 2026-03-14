from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class TransformWarning:
    message: str
    details: Dict[str, Any]


def _coerce_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _melt(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    id_vars = params.get("id_vars")
    value_vars = params.get("value_vars")
    var_name = params.get("var_name", "variable")
    value_name = params.get("value_name", "value")
    if not id_vars:
        id_vars = [c for c in df.columns if df[c].dtype == "O"][:1]
    if not id_vars and df.shape[1] > 1:
        id_vars = [df.columns[0]]
    return pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name=var_name, value_name=value_name)


def _pivot(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    idx = params.get("index")
    columns = params.get("columns")
    values = params.get("values")
    aggfunc = params.get("aggfunc", "mean")
    return df.pivot_table(index=idx, columns=columns, values=values, aggfunc=aggfunc).reset_index()


def _aggregate(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    by = params.get("by")
    col = params.get("column")
    agg = params.get("agg", "mean")
    if by is None or col is None:
        return df
    return df.groupby(by, dropna=False)[col].agg(agg).reset_index(name=f"{col}_{agg}")


def _filter_rows(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    out = df.copy()
    for expr in params.get("expr", []):
        out = out.query(expr)
    return out


def _clip(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    column = params.get("column")
    lo = params.get("low")
    hi = params.get("high")
    if column not in df:
        return df
    out = df.copy()
    if lo is not None:
        out[column] = out[column].clip(lower=lo)
    if hi is not None:
        out[column] = out[column].clip(upper=hi)
    return out


def _rank(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    column = params.get("column")
    out = df.copy()
    if column in out:
        out[f"{column}_rank"] = out[column].rank(method="average")
    return out


def _bin(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    column = params.get("column")
    bins = int(params.get("bins", 10))
    out = df.copy()
    if column in out:
        out[f"{column}_bin"] = pd.cut(_coerce_numeric(out[column]), bins=bins)
    return out


def _moving_window(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    column = params.get("column")
    window = int(params.get("window", 5))
    out = df.copy()
    if column in out:
        out[f"{column}_ma"] = _coerce_numeric(out[column]).rolling(window=window, min_periods=1).mean()
    return out


def _fdr_filter(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    column = params.get("column")
    alpha = float(params.get("alpha", 0.05))
    if column not in df:
        return df
    p = _coerce_numeric(df[column]).to_numpy()
    p = p[np.isfinite(p)]
    if len(p) == 0:
        return df
    order = np.argsort(p)
    ranked = p[order]
    n = len(p)
    cutoff = ranked[np.where(ranked <= (np.arange(1, n + 1) / n) * alpha)[0][-1]] if np.any(ranked <= (np.arange(1, n + 1) / n) * alpha) else None
    if cutoff is None:
        return df.iloc[:0].copy()
    return df.loc[pd.to_numeric(df[column], errors="coerce") <= cutoff]


def _ci_from_bootstrap(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    column = params.get("column")
    group = params.get("group")
    alpha = float(params.get("alpha", 0.05))
    if column not in df:
        return df
    grp = df.groupby(group) if group in df else [(None, df)]
    rows = []
    for g, sub in grp:
        x = _coerce_numeric(sub[column]).dropna()
        if x.empty:
            continue
        lo = x.quantile(alpha / 2)
        hi = x.quantile(1 - alpha / 2)
        rows.append({
            group if group else "group": g,
            "ci_low": lo,
            "ci_high": hi,
            "mean": x.mean(),
        })
    if not rows:
        return df
    return pd.DataFrame(rows)


TRANSFORMS = {
    "melt": _melt,
    "pivot": _pivot,
    "aggregate": _aggregate,
    "filter": _filter_rows,
    "clip": _clip,
    "rank": _rank,
    "bin": _bin,
    "moving_window": _moving_window,
    "fdr_filter": _fdr_filter,
    "ci_from_bootstrap": _ci_from_bootstrap,
}


def transform_factory(op: str):
    return TRANSFORMS.get(op)


def apply_transforms(df: pd.DataFrame, transform_specs: Iterable[Dict[str, Any]]) -> Tuple[pd.DataFrame, List[TransformWarning]]:
    out = df
    warnings: List[TransformWarning] = []
    for spec in transform_specs or []:
        op = spec.get("op") if isinstance(spec, dict) else getattr(spec, "op", None)
        params = spec.get("params", {}) if isinstance(spec, dict) else getattr(spec, "params", {})
        fn = transform_factory(op)
        if fn is None:
            warnings.append(TransformWarning(message=f"Unknown transform '{op}'", details={"transform": op}))
            continue
        try:
            out = fn(out, params or {})
        except Exception as exc:
            warnings.append(TransformWarning(message=f"Transform '{op}' failed", details={"transform": op, "error": str(exc)}))
    return out, warnings


def infer_missing_columns(df: pd.DataFrame, required: List[str], available_map: Optional[Dict[str, str]] = None):
    available = set(df.columns)
    provided = set(required)
    missing = list(provided - available)
    suggestions = {}
    for col in missing:
        if available_map and col in available_map:
            suggestions[col] = available_map[col]
        else:
            suggestions[col] = None
    return missing, suggestions


def suggest_mappings(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    columns = [c.lower() for c in df.columns]
    result = {
        "x": next((c for c in columns if "x" in c or "time" in c or "index" in c), None),
        "y": next((c for c in columns if "y" in c or "value" in c or "score" in c), None),
        "group": next((c for c in columns if "group" in c or "condition" in c), None),
        "category": next((c for c in columns if "class" in c or "category" in c or "label" in c), None),
    }
    # map back to original case
    lookup = {c.lower(): c for c in df.columns}
    return {k: lookup.get(v) if v else None for k, v in result.items()}

