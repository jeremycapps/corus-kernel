"""Surface Agent — plain English readout from derived context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from corus_agents.tasks import AgentTaskResult, build_moment


def render_readout(derive_output: dict[str, Any]) -> str:
    """Render a plain English readout from derived context JSON."""
    lines: list[str] = []

    answer = derive_output.get("answer", "")
    if answer:
        lines.append("Summary")
        lines.append(answer)
        lines.append("")

    context_state = derive_output.get("derived", {}).get("context_state", {})
    if context_state:
        lines.append("Coordination")
        lines.append(
            f"  Status: {context_state.get('coordination', 'unknown')}"
        )
        lines.append(f"  Reason: {context_state.get('reason', 'unknown')}")
        lines.append("")

    contexts = derive_output.get("derived", {}).get("contexts", [])
    if contexts:
        ctx = contexts[0]
        lines.append("Boundary context")
        if ctx.get("boundary_id"):
            lines.append(f"  Boundary: {ctx['boundary_id']}")
        if ctx.get("subject"):
            lines.append(f"  Subject: {ctx['subject']}")
        if ctx.get("orchestrator"):
            lines.append(f"  Orchestrator: {ctx['orchestrator']}")
        if ctx.get("team_id"):
            lines.append(f"  Team: {ctx['team_id']}")
        lines.append("")

        selected_artifacts = ctx.get("selected_artifacts", [])
        if selected_artifacts:
            lines.append("Selected artifacts")
            statuses = {
                item["artifact_id"]: item["status"]
                for item in derive_output.get("derived", {}).get("artifact_statuses", [])
            }
            for artifact_id in selected_artifacts:
                status = statuses.get(artifact_id, "unknown")
                lines.append(f"  - {artifact_id} ({status})")
            lines.append("")

        selected_contracts = ctx.get("selected_contracts", [])
        if selected_contracts:
            lines.append("Selected contracts")
            for contract_id in selected_contracts:
                lines.append(f"  - {contract_id}")
            lines.append("")

    warnings = derive_output.get("warnings", [])
    if warnings:
        lines.append("Warnings")
        for warning in warnings:
            lines.append(f"  - {warning}")
        lines.append("")

    trace_claims = derive_output.get("trace", {}).get("claims", [])
    if trace_claims:
        lines.append("Trace")
        for claim in trace_claims:
            lines.append(f"  - {claim}")

    return "\n".join(lines).strip() + "\n"


def run(
    fixture_dir: Path,
    *,
    derive_output: dict[str, Any] | None = None,
    derive_path: Path | None = None,
) -> AgentTaskResult:
    """
    Render plain English readout from derived context JSON.

    Does not modify declared objects or derive new context unless
    derive_output is not supplied (reads derive.output.json).
    """
    fixture_dir = Path(fixture_dir)
    if derive_output is None:
        path = derive_path or (fixture_dir / "derive.output.json")
        if not path.exists():
            raise FileNotFoundError(
                f"Derived context not found: {path}. Run derive agent first."
            )
        derive_output = json.loads(path.read_text(encoding="utf-8"))

    readout = render_readout(derive_output)
    readout_path = fixture_dir / "explain.md"
    readout_path.write_text(readout, encoding="utf-8")

    return AgentTaskResult(
        agent="surface",
        verb="agent.explain",
        fixture_dir=fixture_dir,
        outputs={
            "readout": readout,
            "readout_path": str(readout_path),
        },
        moment=build_moment(
            "agent.explain",
            str(readout_path),
            moment_id="moment.runtime.explain",
        ),
    )
