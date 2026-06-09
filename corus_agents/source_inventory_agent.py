"""Source inventory agent — generic source declarations from raw files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from corus_agents.source_text import re_slug
from corus_agents.tasks import AgentTaskResult

SOURCES_YAML = "sources/sources.yaml"


def infer_source_declaration(raw_path: Path) -> dict[str, str]:
    """
    Build a generic source declaration from a raw filename.

    Does not infer roles, artifacts, contracts, teams, profiles, or boundaries.
    """
    slug = re_slug(raw_path.stem)
    return {
        "id": f"source.{slug}",
        "type": "document",
        "label": raw_path.stem,
        "locator": f"sources/raw/{raw_path.name}",
    }


def inventory_raw_sources(fixture_dir: Path) -> list[dict[str, Any]]:
    """List generic source declarations from sources/raw/."""
    raw_dir = Path(fixture_dir) / "sources" / "raw"
    if not raw_dir.exists():
        return []

    declarations: list[dict[str, Any]] = []
    for path in sorted(raw_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".pdf", ".txt", ".md"}:
            continue
        declarations.append(infer_source_declaration(path))
    return declarations


def write_sources_yaml(fixture_dir: Path, sources: list[dict[str, Any]]) -> Path:
    path = Path(fixture_dir) / SOURCES_YAML
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump({"sources": sources}, handle, default_flow_style=False, sort_keys=False)
    return path


def run(fixture_dir: Path, *, force: bool = False) -> AgentTaskResult:
    """
    Inventory raw source files and write sources/sources.yaml when missing.

    Never infers declared Corus objects beyond generic source declarations.
    """
    fixture_dir = Path(fixture_dir)
    sources_path = fixture_dir / SOURCES_YAML

    if sources_path.exists() and not force:
        data = yaml.safe_load(sources_path.read_text(encoding="utf-8")) or {}
        sources = list(data.get("sources", []))
        wrote = False
    else:
        sources = inventory_raw_sources(fixture_dir)
        if not sources_path.exists() or force:
            write_sources_yaml(fixture_dir, sources)
            wrote = True
        else:
            wrote = False

    return AgentTaskResult(
        agent="source_inventory",
        verb="agent.interpret",
        fixture_dir=fixture_dir,
        outputs={
            "sources_yaml": str(sources_path),
            "source_count": len(sources),
            "wrote_sources_yaml": wrote,
        },
        moment=None,
    )


def load_sources(fixture_dir: Path) -> list[dict[str, Any]]:
    """Load source declarations, inventorying raw files when YAML is absent."""
    fixture_dir = Path(fixture_dir)
    sources_path = fixture_dir / SOURCES_YAML
    if sources_path.exists():
        data = yaml.safe_load(sources_path.read_text(encoding="utf-8")) or {}
        return list(data.get("sources", []))
    sources = inventory_raw_sources(fixture_dir)
    if sources:
        write_sources_yaml(fixture_dir, sources)
    return sources
