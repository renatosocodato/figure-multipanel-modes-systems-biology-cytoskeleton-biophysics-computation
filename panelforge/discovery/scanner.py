from __future__ import annotations

import fnmatch
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class DiscoveryResult:
    root: str
    phase: str
    files: List[Path]


def _match_any(path: str, patterns: List[str]) -> bool:
    if not patterns:
        return False
    candidate = str(path).replace("\\", "/")
    leaf = candidate.rsplit("/", 1)[-1]
    normalized = candidate.strip("/")
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern):
            return True
        if fnmatch.fnmatch(leaf, pattern):
            return True
        if fnmatch.fnmatch(f"*/{leaf}", pattern):
            return True
    return False


def _walk_dirs(root: Path, max_depth: int) -> Set[Path]:
    found: Set[Path] = set()
    q = deque([(root, 0)])
    while q:
        folder, depth = q.popleft()
        found.add(folder)
        if depth >= max_depth:
            continue
        for child in folder.iterdir():
            if not child.is_dir():
                continue
            if child.name.startswith(".") or child.name == "__pycache__":
                continue
            q.append((child, depth + 1))
    return found


def discover_analysis_roots(roots: List[str], include: List[str], exclude: List[str], max_depth: int = 8) -> List[DiscoveryResult]:
    include_patterns = include or ["analysis_*", "*analysis*"]
    exclude_patterns = exclude or [".git", ".venv", "__pycache__", "tmp"]
    results: List[DiscoveryResult] = []
    for root in roots:
        root_path = Path(root).expanduser().resolve()
        if not root_path.exists():
            continue
        candidates: Set[Path] = set()
        for pattern in include_patterns:
            for match in root_path.rglob(pattern):
                if match.is_dir():
                    rel_parts = match.relative_to(root_path).parts
                    if len(rel_parts) <= max_depth:
                        candidates.add(match)

        if not candidates:
            candidates = {
                candidate
                for candidate in _walk_dirs(root_path, max_depth)
                if _match_any(candidate.relative_to(root_path).as_posix(), include_patterns)
            }

        for base in sorted(candidates):
            rel = base.relative_to(root_path).as_posix()
            if _match_any(rel, exclude_patterns):
                continue
            if not _match_any(rel, include_patterns):
                continue
            phase = base.name
            files = sorted([p for p in base.glob("**/*") if p.is_file() and not p.name.startswith(".")])
            results.append(DiscoveryResult(root=str(base), phase=phase, files=files))
    return results


def phase_discovery(roots: List[str], include: List[str], exclude: List[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for hit in discover_analysis_roots(roots, include, exclude):
        out.setdefault(hit.phase, []).append(hit.root)
    return out
