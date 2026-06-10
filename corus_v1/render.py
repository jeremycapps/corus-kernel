"""Render Corus v1 coordination state from derived contract vectors."""

from __future__ import annotations

from typing import Any


def _agent_labels(bundle: dict[str, Any]) -> dict[str, str]:
    return {
        agent["id"]: agent["label"]
        for agent in bundle.get("agents", {}).get("agents", [])
    }


def _format_contract_state(state: dict[str, Any], labels: dict[str, str]) -> str:
    owner = labels.get(state["owner"], state["owner"])
    executor = labels.get(state["executor"], state["executor"])
    consumer = labels.get(state["consumer"], state["consumer"])
    return (
        f"  - {state['id']}: readiness={state['readiness']}, output={state['output']} "
        f"(owner={owner}, executor={executor}, consumer={consumer})"
    )


def render(bundle: dict[str, Any], derived: dict[str, Any]) -> str:
    """Render declared intent and derived contract state."""
    project = bundle.get("project", {})
    labels = _agent_labels(bundle)
    derived_state = derived["derived"]
    objectives = bundle.get("objectives", {}).get("objectives", [])

    lines = [
        project.get("name", "Corus v1 Self-Build"),
        "",
        "Contracts instruct. Artifacts report. Reducers derive.",
        "",
    ]

    lines.append("Agents")
    for agent in bundle.get("agents", {}).get("agents", []):
        lines.append(f"  - {agent['label']} ({agent['id']})")
    lines.append("")

    lines.append("Objectives")
    for objective in objectives:
        state = (
            "satisfied"
            if any(item["id"] == objective["id"] for item in derived_state["satisfied_objectives"])
            else "active"
        )
        lines.append(f"  - [{state}] {objective.get('intent', objective['id'])}")
    lines.append("")

    lines.append("Contract states")
    for state in derived_state["contract_states"]:
        lines.append(_format_contract_state(state, labels))
    lines.append("")

    lines.append("Derived summary")
    lines.append(f"  blocked_contracts: {derived_state['blocked_contracts']}")
    lines.append(f"  unblocked_contracts: {derived_state['unblocked_contracts']}")
    lines.append(f"  submitted_contracts: {derived_state['submitted_contracts']}")
    lines.append(f"  satisfied_contracts: {derived_state['satisfied_contracts']}")
    lines.append(f"  rejected_contracts: {derived_state['rejected_contracts']}")
    lines.append("")

    return "\n".join(lines).strip() + "\n"
