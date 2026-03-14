from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..schema import PaletteSpec

COLORBREWER = {
    "qualitative": {
        "Set2": ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3"],
        "Set1": ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf"],
        "Paired": ["#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#fb9a99", "#e31a1c", "#fdbf6f", "#ff7f00"],
    },
    "sequential": {
        "Blues": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"],
        "Greens": ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#006d2c", "#00441b"],
        "Oranges": ["#fff5eb", "#fee6ce", "#fdd0a2", "#fdae6b", "#fd8d3c", "#f16913", "#d94801", "#a63603", "#7f2704"],
    },
    "diverging": {
        "RdBu": ["#b2182b", "#ef8a62", "#fddbc7", "#f7f7f7", "#d1e5f0", "#67a9cf", "#2166ac"],
        "Spectral": ["#d7191c", "#fdae61", "#ffffbf", "#abd9e9", "#2c7bb6"],
    },
    "mixed": {
        "Muted": ["#CC6677", "#332288", "#117733", "#44AA99", "#88CCEE", "#DDCC77", "#AA4499", "#882255", "#999933"],
    },
}


def _to_hex(color: Tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color)


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    v = value.lstrip("#")
    return tuple(int(v[i : i + 2], 16) for i in (0, 2, 4))


def _srgb_channel_to_linear(v: int) -> float:
    cs = v / 255.0
    return cs / 12.92 if cs <= 0.03928 else ((cs + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    r, g, b = (_srgb_channel_to_linear(x) for x in _hex_to_rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(a: str, b: str) -> float:
    l1 = _luminance(a)
    l2 = _luminance(b)
    light = max(l1, l2) + 0.05
    dark = min(l1, l2) + 0.05
    return light / dark


def _mutate_color(hex_color: str, mode: str, shift: int) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    if mode == "muted":
        factor = 0.80
    elif mode == "contrast_boost":
        factor = 1.15
    elif mode == "status_shift":
        factor = 0.9
    elif mode == "emphasis":
        factor = 1.05
    else:
        factor = 1.0

    phase = (shift % 90) / 90.0
    r = min(255, max(0, int(r * factor + 8 * phase)))
    g = min(255, max(0, int(g * factor + 8 * phase)))
    b = min(255, max(0, int(b * factor + 8 * phase)))
    return _to_hex((r, g, b))


def _check_min_contrast(palette: List[str], min_ratio: float = 1.8) -> bool:
    if len(palette) < 2:
        return True
    for i, a in enumerate(palette[:-1]):
        for b in palette[i + 1 :]:
            if _contrast_ratio(a, b) < min_ratio:
                return False
    return True


@dataclass
class PaletteEngine:
    spec: PaletteSpec

    def _select_family(self) -> str:
        if self.spec.source != "colorbrewer":
            return "qualitative"
        if self.spec.family in COLORBREWER:
            return self.spec.family
        return "mixed"

    def _select_palette(self, family: str) -> Tuple[str, List[str]]:
        names = list(COLORBREWER[family].keys())
        if not names:
            names = ["Set2"]
            return names[0], COLORBREWER["qualitative"]["Set2"]
        idx = int(self.spec.seed or 0)
        palette_name = self.spec.palette or names[idx % len(names)]
        if palette_name not in COLORBREWER[family]:
            palette_name = names[idx % len(names)]
        return palette_name, COLORBREWER[family][palette_name][:]

    def _resolve_mutation_mode(self, family: str) -> str:
        role_modes = {"primary": "none", "comparison": "contrast_boost", "annotation": "muted", "status": "status_shift"}
        if self.spec.mutation_mode and self.spec.mutation_mode != "none":
            return self.spec.mutation_mode
        return role_modes.get(self.spec.role, "none")

    def resolve(self, n: int) -> Dict[str, object]:
        family = self._select_family()
        palette_name, palette_base = self._select_palette(family)
        mutation_mode = self._resolve_mutation_mode(family)
        seed = int(self.spec.seed or 0)
        role_shift = abs(hash((seed, palette_name, self.spec.role)) % (10**8))
        seed_hash = hashlib.md5(f"{seed}:{palette_name}:{self.spec.role}:{self.spec.source}".encode()).hexdigest()

        palette = [
            _mutate_color(color, mutation_mode, role_shift + idx)
            for idx, color in enumerate(palette_base)
        ]

        if not _check_min_contrast(palette, min_ratio=1.5):
            muted = [
                _mutate_color(color, "muted", role_shift + idx * 2)
                for idx, color in enumerate(palette_base)
            ]
            if _check_min_contrast(muted, min_ratio=1.5):
                palette = muted

        palette = palette[: max(1, n)] if n else palette
        palette_id = f"{self.spec.source}:{family}:{palette_name}:{self.spec.role}"

        return {
            "palette_id": palette_id,
            "palette_mutation": mutation_mode,
            "palette_hash": hashlib.md5("|".join(palette).encode()).hexdigest(),
            "seed": seed,
            "seed_hash": seed_hash,
            "role": self.spec.role,
            "colors": palette,
        }


def resolve_palette(spec: PaletteSpec, n_colors: int) -> Dict[str, object]:
    if spec is None:
        spec = PaletteSpec()
    return PaletteEngine(spec=spec).resolve(n_colors)
