"""Admission Agent — compare candidates to admitted objects."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from corus_agents.tasks import AgentTaskResult, build_moment

ADMISSION_REPORT = "admission_report.json"
CANDIDATE_TO_ADMITTED = {
    "artifacts.candidate.yaml": "artifacts.yaml",
    "contracts.candidate.yaml": "contracts.yaml",
    "roles.candidate.yaml": "roles.yaml",
    "teams.candidate.yaml": "teams.yaml",
    "profiles.candidate.yaml": "profiles.yaml",
    "boundaries.candidate.yaml": "boundaries.yaml",
    "moments.candidate.yaml": "moments.yaml",
    "timpos.candidate.yaml": "timpos.yaml",
}
ARTIFACTS_CANDIDATE = "artifacts.candidate.yaml"
ARTIFACTS_ADMITTED = "artifacts.yaml"
CONTRACTS_CANDIDATE = "contracts.candidate.yaml"
CONTRACTS_ADMITTED = "contracts.yaml"


def _load_yaml_list(path: Path, key: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get(key, []))


def _compare_candidates(
    candidates: list[dict[str, Any]],
    admitted: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_ids = {item["id"] for item in candidates}
    admitted_ids = {item["id"] for item in admitted}
    return {
        "candidate_ids": sorted(candidate_ids),
        "admitted_ids": sorted(admitted_ids),
        "only_in_candidates": sorted(candidate_ids - admitted_ids),
        "only_in_admitted": sorted(admitted_ids - candidate_ids),
        "shared_ids": sorted(candidate_ids & admitted_ids),
        "candidates_match_admitted": candidates == admitted,
    }


def build_report(fixture_dir: Path) -> dict[str, Any]:
    fixture_dir = Path(fixture_dir)
    artifact_candidates = _load_yaml_list(fixture_dir / ARTIFACTS_CANDIDATE, "artifacts")
    artifact_admitted = _load_yaml_list(fixture_dir / ARTIFACTS_ADMITTED, "artifacts")
    contract_candidates = _load_yaml_list(fixture_dir / CONTRACTS_CANDIDATE, "contracts")
    contract_admitted = _load_yaml_list(fixture_dir / CONTRACTS_ADMITTED, "contracts")

    return {
        "fixture_dir": str(fixture_dir),
        "artifacts": _compare_candidates(artifact_candidates, artifact_admitted),
        "contracts": _compare_candidates(contract_candidates, contract_admitted),
        "ready_to_admit": (
            artifact_candidates != []
            and contract_candidates != []
            and (
                artifact_candidates != artifact_admitted
                or contract_candidates != contract_admitted
            )
        ),
    }


def run(fixture_dir: Path, *, approve: bool = False) -> AgentTaskResult:
    """
    Compare candidates to admitted objects and write admission_report.json.

    Promotion to admitted YAML occurs only when approve=True.
    """
    fixture_dir = Path(fixture_dir)
    report = build_report(fixture_dir)
    report["approved"] = approve
    report["promoted"] = False

    report_path = fixture_dir / ADMISSION_REPORT
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if approve:
        _promote_candidates(fixture_dir)
        report["promoted"] = True
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verb = "agent.admit" if approve else "agent.admission_report"
    return AgentTaskResult(
        agent="admission",
        verb=verb,
        fixture_dir=fixture_dir,
        outputs={
            "admission_report": str(report_path),
            "ready_to_admit": report["ready_to_admit"],
            "promoted": report["promoted"],
        },
        moment=build_moment(
            verb,
            str(fixture_dir),
            moment_id=f"moment.runtime.{verb.removeprefix('agent.')}",
        ),
    )


def _promote_candidates(fixture_dir: Path) -> None:
    promoted_any = False
    for candidate_name, admitted_name in CANDIDATE_TO_ADMITTED.items():
        candidate_path = fixture_dir / candidate_name
        if not candidate_path.exists():
            continue
        shutil.copy2(candidate_path, fixture_dir / admitted_name)
        promoted_any = True
    if not promoted_any:
        raise FileNotFoundError("Cannot promote: no candidate YAML files found")
