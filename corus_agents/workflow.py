"""Workflow gates — admission and review checkpoints."""

from __future__ import annotations

from pathlib import Path

from corus_agents import admission_agent

ARTIFACTS_CANDIDATE = "artifacts.candidate.yaml"
CONTRACTS_CANDIDATE = "contracts.candidate.yaml"


def admission_required(fixture_dir: Path) -> bool:
    """True when candidates exist and differ from admitted YAML."""
    fixture_dir = Path(fixture_dir)
    if not (fixture_dir / ARTIFACTS_CANDIDATE).exists():
        return False
    if not (fixture_dir / CONTRACTS_CANDIDATE).exists():
        return False
    report = admission_agent.build_report(fixture_dir)
    return bool(report.get("ready_to_admit"))


def review_required(fixture_dir: Path) -> bool:
    """True when an admission report exists and promotion has not occurred."""
    fixture_dir = Path(fixture_dir)
    report_path = fixture_dir / admission_agent.ADMISSION_REPORT
    if not report_path.exists():
        return admission_required(fixture_dir)
    import json

    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("promoted"):
        return False
    return bool(report.get("ready_to_admit"))


def derive_blocked_reason(fixture_dir: Path) -> str | None:
    """Return a message when derive must not proceed until admission."""
    if review_required(fixture_dir):
        return (
            "Derive blocked: admission review required. "
            "Candidates differ from admitted YAML. "
            "Run `corus_agents admit <fixture> --approve` after explicit review."
        )
    return None


def run_pipeline(
    fixture_dir: Path,
    *,
    boundary_id: str | None = None,
) -> tuple[int, str]:
    """
    Run interpret → admission-report → derive → audit → explain.

    Stops with admission/review required before derive when candidates
    differ from admitted YAML.
    """
    from corus_agents import audit_agent, derive_agent, interpreter_agent, surface_agent

    fixture_dir = Path(fixture_dir)

    interpreter_agent.run(fixture_dir)
    admission_agent.run(fixture_dir, approve=False)

    if review_required(fixture_dir):
        return (
            2,
            "Admission review required. "
            "Run: corus_agents admit <fixture> --approve",
        )

    derive_agent.run(fixture_dir, boundary_id=boundary_id)
    audit_result = audit_agent.run(fixture_dir, boundary_id=boundary_id)
    surface_agent.run(fixture_dir)

    if not audit_result.outputs["passed"]:
        return (1, "Audit failed.")

    return (0, "Pipeline complete.")
