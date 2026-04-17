"""Dynamics registry for phase_portrait chart type.

Provides a registry of RHS functions callable as f(state) -> (dx, dy).
Users can extend by registering new systems.
"""
from .rhoa import (
    rhoa_tristable_v1,
    U as rhoa_U,
    dU_dx as rhoa_dU_dx,
    find_fixed_points as rhoa_find_fixed_points,
)

RHS_REGISTRY = {
    "rhoa_tristable_v1": rhoa_tristable_v1,
}

POTENTIAL_REGISTRY = {
    "rhoa_tristable_v1": rhoa_U,
}

__all__ = [
    "RHS_REGISTRY",
    "POTENTIAL_REGISTRY",
    "rhoa_tristable_v1",
    "rhoa_U",
    "rhoa_dU_dx",
    "rhoa_find_fixed_points",
]
