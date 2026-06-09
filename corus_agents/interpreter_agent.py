"""Interpreter Agent — produce candidate artifacts and contracts with evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from corus_agents.bootstrap_interpreter import bootstrap
from corus_kernel.loader import INTERPRET_CANDIDATE_FILES

from corus_agents.tasks import AgentTaskResult, build_moment

ADMITTED_FILES = (
    "artifacts.yaml",
    "contracts.yaml",
    "roles.yaml",
    "teams.yaml",
    "profiles.yaml",
    "boundaries.yaml",
    "moments.yaml",
    "timpos.yaml",
)


def run(fixture_dir: Path) -> AgentTaskResult:
    """
    Bootstrap interpretation from source files and write candidates only.

    Never promotes candidates to admitted YAML.
    """
    fixture_dir = Path(fixture_dir)
    admitted_before = _snapshot_admitted(fixture_dir)

    result = bootstrap(fixture_dir)

    admitted_after = _snapshot_admitted(fixture_dir)
    if admitted_before != admitted_after:
        raise RuntimeError("Interpreter Agent must not modify admitted declared YAML")

    outputs = {
        "artifacts_candidate": str(fixture_dir / "artifacts.candidate.yaml"),
        "contracts_candidate": str(fixture_dir / "contracts.candidate.yaml"),
        "bootstrap_report": str(fixture_dir / "bootstrap_report.json"),
        "interpretation_trace": str(fixture_dir / "interpretation_trace.json"),
        "artifact_count": len(result["artifacts"]),
        "contract_count": len(result["contracts"]),
    }

    return AgentTaskResult(
        agent="interpreter",
        verb="agent.interpret",
        fixture_dir=fixture_dir,
        outputs=outputs,
        moment=build_moment(
            "agent.interpret",
            str(fixture_dir),
            moment_id="moment.runtime.interpret",
        ),
    )


def _snapshot_admitted(fixture_dir: Path) -> dict[str, str | None]:
    snapshots: dict[str, str | None] = {}
    for name in ADMITTED_FILES:
        path = fixture_dir / name
        snapshots[name] = path.read_text(encoding="utf-8") if path.exists() else None
    return snapshots


def candidate_files_written(fixture_dir: Path) -> list[Path]:
    fixture_dir = Path(fixture_dir)
    names = list(INTERPRET_CANDIDATE_FILES) + [
        "bootstrap_report.json",
        "roles.candidate.yaml",
        "teams.candidate.yaml",
        "profiles.candidate.yaml",
        "boundaries.candidate.yaml",
        "moments.candidate.yaml",
        "timpos.candidate.yaml",
    ]
    return [fixture_dir / name for name in names if (fixture_dir / name).exists()]


def read_trace(fixture_dir: Path) -> list[dict[str, Any]]:
    path = Path(fixture_dir) / "interpretation_trace.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
