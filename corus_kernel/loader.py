"""Load declared object bundles from fixture directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Files read by derive. Candidate files from interpret are never loaded here.
DERIVE_BUNDLE_FILES: dict[str, str] = {
    "artifacts": "artifacts.yaml",
    "contracts": "contracts.yaml",
    "roles": "roles.yaml",
    "teams": "teams.yaml",
    "profiles": "profiles.yaml",
    "boundaries": "boundaries.yaml",
    "moments": "moments.yaml",
    "timpos": "timpos.yaml",
}

# Written by interpret; gitignored; not used by derive.
INTERPRET_CANDIDATE_FILES = (
    "artifacts.candidate.yaml",
    "contracts.candidate.yaml",
    "interpretation_trace.json",
)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_bundle(fixture_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """
    Load admitted declared objects for derive.

    Only reads artifacts.yaml and contracts.yaml (not *.candidate.yaml).
    Sources are loaded from sources/sources.yaml; raw PDFs are never parsed.
    """
    fixture_dir = Path(fixture_dir)
    bundle: dict[str, list[dict[str, Any]]] = {}

    sources_path = fixture_dir / "sources" / "sources.yaml"
    sources_data = _read_yaml(sources_path)
    bundle["sources"] = list(sources_data.get("sources", []))

    for collection, filename in DERIVE_BUNDLE_FILES.items():
        if filename.endswith(".candidate.yaml"):
            raise ValueError(f"derive must not read candidate file: {filename}")
        data = _read_yaml(fixture_dir / filename)
        bundle[collection] = list(data.get(collection, []))

    return bundle


def load_sources(fixture_dir: Path) -> list[dict[str, Any]]:
    """Load only source declarations."""
    fixture_dir = Path(fixture_dir)
    data = _read_yaml(fixture_dir / "sources" / "sources.yaml")
    return list(data.get("sources", []))


def index_by_id(collection: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in collection}
