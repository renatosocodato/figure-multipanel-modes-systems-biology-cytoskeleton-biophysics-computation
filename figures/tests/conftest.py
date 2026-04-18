"""Shared test fixtures — enforce non-interactive backend before any import."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg", force=True)
