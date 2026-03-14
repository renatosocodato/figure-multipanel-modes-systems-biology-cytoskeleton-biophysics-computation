from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import platform
import subprocess

from ..schema import RunManifest


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_sha() -> Optional[str]:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


@dataclass
class ManifestBuilder:
    spec_path: Optional[Path] = None
    command: str = "panelforge"
    figure: Optional[Dict[str, Any]] = None
    spec_signature: Optional[str] = None
    panels: List[Dict[str, Any]] = field(default_factory=list)
    palette: Dict[str, Any] = field(default_factory=dict)
    figures: List[Dict[str, Any]] = field(default_factory=list)

    def add_panel(self, panel_label: str, status: str, file_path: Path, width_in: float, height_in: float) -> None:
        self.panels.append(
            {
                "panel_label": panel_label,
                "status": status,
                "file": str(file_path),
                "checksum": _compute_sha256(file_path),
                "width_in": width_in,
                "height_in": height_in,
            }
        )

    def add_figure(self, figure_label: str, status: str, file_path: Path, width_in: float, height_in: float) -> None:
        self.figures.append(
            {
                "label": figure_label,
                "status": status,
                "file": str(file_path),
                "checksum": _compute_sha256(file_path),
                "width_in": width_in,
                "height_in": height_in,
            }
        )

    def build(self) -> RunManifest:
        return RunManifest(
            schema_version="1.0.0",
            command=self.command,
            timestamp=datetime.now(timezone.utc).isoformat(),
            git_sha=_git_sha(),
            spec_path=str(self.spec_path) if self.spec_path else None,
            spec_signature=self.spec_signature,
            figure=self.figure or {},
            panels=self.panels,
            figures=self.figures,
            environment={
                "python": platform.python_version(),
                "platform": platform.platform(),
            },
            palette=self.palette,
        )


def save_manifest(builder: ManifestBuilder, path: Path) -> Path:
    payload = builder.build().model_dump()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2)
    return path
