"""Load Corus v1 self-build project bundles from .corus/."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CORUS_DIR = ".corus"

REQUIRED_BUNDLE_FILES: dict[str, str] = {
    "project": "project.yaml",
    "agents": "agents.yaml",
    "objectives": "objectives.yaml",
    "artifacts": "artifacts.yaml",
    "contracts": "contracts.yaml",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_project(project_dir: Path | str) -> dict[str, Any]:
    """Load the Corus v1 project bundle from project_dir/.corus/."""
    project_dir = Path(project_dir)
    corus_dir = project_dir / CORUS_DIR
    if not corus_dir.is_dir():
        raise FileNotFoundError(f"Missing Corus project directory: {corus_dir}")

    bundle: dict[str, Any] = {"project_dir": str(project_dir)}
    for key, filename in REQUIRED_BUNDLE_FILES.items():
        path = corus_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing required Corus bundle file: {path}")
        bundle[key] = _load_yaml(path)

    return bundle


def index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def default_project_dir() -> Path:
    """Return repository root containing .corus/."""
    return Path(__file__).resolve().parent.parent
