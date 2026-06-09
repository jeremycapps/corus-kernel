"""Generic source interpretation interface."""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from corus_kernel.loader import load_sources

FIXTURE_INTERPRETER_FILENAME = "interpret_fixture.py"

InterpretFn = Callable[[list[dict[str, Any]], Path], dict[str, Any]]


def _source_ids(sources: list[dict[str, Any]]) -> set[str]:
    return {s["id"] for s in sources}


def load_fixture_interpreter(fixture_dir: Path) -> InterpretFn | None:
    """
    Load optional fixture-local interpreter module (test machinery).

    Fixture interpreters live beside fixture YAML and are not part of the
    declared Corus object model.
    """
    path = Path(fixture_dir) / FIXTURE_INTERPRETER_FILENAME
    if not path.exists():
        return None
    module_name = f"fixture_interpreter_{path.parent.name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load fixture interpreter from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    interpreter = getattr(module, "interpret", None)
    if interpreter is None or not callable(interpreter):
        raise ImportError(f"{path} must define a callable interpret(sources, fixture_dir)")
    return interpreter


def interpret_sources(
    fixture_dir: Path,
    interpreter: InterpretFn | None = None,
) -> dict[str, Any]:
    """
    Read sources and run an interpreter to produce candidates and trace.

    Sources do not become artifacts silently. Interpretation is explicit and
    fixture-specific logic must be supplied by a fixture interpreter module
    or passed in directly.
    """
    fixture_dir = Path(fixture_dir)
    sources = load_sources(fixture_dir)

    trace_steps: list[dict[str, Any]] = [
        {
            "action": "load_source",
            "detail": f"Loaded {source['id']}",
            "source_id": source["id"],
        }
        for source in sources
    ]

    if interpreter is None:
        interpreter = load_fixture_interpreter(fixture_dir)

    if interpreter is None:
        return {"artifacts": [], "contracts": [], "trace": trace_steps}

    result = interpreter(sources, fixture_dir)
    trace_steps.extend(result.get("trace", []))
    return {
        "artifacts": list(result.get("artifacts", [])),
        "contracts": list(result.get("contracts", [])),
        "trace": trace_steps,
    }


def write_interpretation(
    fixture_dir: Path,
    interpreter: InterpretFn | None = None,
) -> dict[str, Any]:
    """Run interpretation and write candidate files to the fixture directory."""
    fixture_dir = Path(fixture_dir)
    result = interpret_sources(fixture_dir, interpreter=interpreter)

    artifacts_path = fixture_dir / "artifacts.candidate.yaml"
    contracts_path = fixture_dir / "contracts.candidate.yaml"
    trace_path = fixture_dir / "interpretation_trace.json"

    with artifacts_path.open("w", encoding="utf-8") as handle:
        yaml.dump(
            {"artifacts": result["artifacts"]},
            handle,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    with contracts_path.open("w", encoding="utf-8") as handle:
        yaml.dump(
            {"contracts": result["contracts"]},
            handle,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    with trace_path.open("w", encoding="utf-8") as handle:
        json.dump(result["trace"], handle, indent=2, sort_keys=True)
        handle.write("\n")

    return result
