"""Audit Agent — validate invariants and write audit report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from corus_kernel.derive import derive_context
from corus_kernel.loader import DERIVE_BUNDLE_FILES, INTERPRET_CANDIDATE_FILES, load_bundle
from corus_kernel.validate import ValidationError, validate_references, validate_schema, validate_unique_ids

from corus_agents.tasks import AgentTaskResult, build_moment

AUDIT_REPORT = "audit_report.json"


def _check_candidate_isolation(fixture_dir: Path) -> list[str]:
    """Verify derive bundle file list excludes candidate paths."""
    issues: list[str] = []
    for collection, filename in DERIVE_BUNDLE_FILES.items():
        if "candidate" in filename:
            issues.append(f"derive reads candidate collection {collection}: {filename}")
    return issues


def _check_deterministic_hash(fixture_dir: Path, boundary_id: str | None) -> dict[str, Any]:
    first = derive_context(fixture_dir, boundary_id=boundary_id)
    second = derive_context(fixture_dir, boundary_id=boundary_id)
    hash_a = first["hashes"]["content"]
    hash_b = second["hashes"]["content"]
    return {
        "deterministic": hash_a == hash_b,
        "hash": hash_a,
    }


def run(fixture_dir: Path, *, boundary_id: str | None = None) -> AgentTaskResult:
    """
    Validate kernel invariants and write audit_report.json.

    Does not mutate fixture files.
    """
    fixture_dir = Path(fixture_dir)
    snapshot = _snapshot_fixture(fixture_dir)

    checks: dict[str, Any] = {
        "schema_valid": False,
        "references_valid": False,
        "unique_ids_valid": False,
        "candidate_isolation": [],
        "deterministic_hash": {},
        "errors": [],
    }

    try:
        bundle = load_bundle(fixture_dir)
        validate_schema(bundle)
        checks["schema_valid"] = True
    except ValidationError as exc:
        checks["errors"].append(f"schema: {exc}")

    try:
        bundle = load_bundle(fixture_dir)
        validate_unique_ids(bundle)
        checks["unique_ids_valid"] = True
    except ValidationError as exc:
        checks["errors"].append(f"unique_ids: {exc}")

    try:
        bundle = load_bundle(fixture_dir)
        validate_references(bundle)
        checks["references_valid"] = True
    except ValidationError as exc:
        checks["errors"].append(f"references: {exc}")

    isolation_issues = _check_candidate_isolation(fixture_dir)
    checks["candidate_isolation"] = isolation_issues
    if isolation_issues:
        checks["errors"].extend(isolation_issues)

    if checks["schema_valid"] and checks["references_valid"] and checks["unique_ids_valid"]:
        checks["deterministic_hash"] = _check_deterministic_hash(fixture_dir, boundary_id)
        if not checks["deterministic_hash"]["deterministic"]:
            checks["errors"].append("derive output hash is not deterministic")

    checks["passed"] = len(checks["errors"]) == 0

    report_path = fixture_dir / AUDIT_REPORT
    report_path.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _assert_snapshot_unchanged(fixture_dir, snapshot)

    return AgentTaskResult(
        agent="audit",
        verb="agent.audit",
        fixture_dir=fixture_dir,
        outputs={
            "audit_report": str(report_path),
            "passed": checks["passed"],
            "error_count": len(checks["errors"]),
        },
        moment=build_moment(
            "agent.audit",
            str(report_path),
            moment_id="moment.runtime.audit",
        ),
    )


def _snapshot_fixture(fixture_dir: Path) -> dict[str, str | None]:
    names = list(DERIVE_BUNDLE_FILES.values()) + list(INTERPRET_CANDIDATE_FILES)
    names.append("sources/sources.yaml")
    snapshot: dict[str, str | None] = {}
    for name in names:
        path = fixture_dir / name
        snapshot[name] = path.read_text(encoding="utf-8") if path.exists() else None
    return snapshot


def _assert_snapshot_unchanged(fixture_dir: Path, before: dict[str, str | None]) -> None:
    after = _snapshot_fixture(fixture_dir)
    if before != after:
        raise RuntimeError("Audit Agent must not mutate fixture files")
