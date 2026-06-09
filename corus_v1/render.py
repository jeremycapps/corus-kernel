"""Render Corus v1 self-build surfaces."""

from __future__ import annotations

from typing import Any


def _agent_labels(bundle: dict[str, Any]) -> dict[str, str]:
    agents = bundle.get("agents", {}).get("agents", [])
    return {agent["id"]: agent["label"] for agent in agents}


def _surface_agents(bundle: dict[str, Any], surface: str) -> list[dict[str, Any]]:
    return [
        agent for agent in bundle.get("agents", {}).get("agents", [])
        if agent.get("surface") == surface
    ]


def _objectives_for_surface(derived: dict[str, Any], surface: str) -> list[dict[str, Any]]:
    active = derived["derived"]["active_objectives"]
    satisfied = derived["derived"]["satisfied_objectives"]
    return [
        *[
            {**objective, "state": "active"}
            for objective in active
            if objective.get("surface") == surface
        ],
        *[
            {**objective, "state": "satisfied"}
            for objective in satisfied
            if objective.get("surface") == surface
        ],
    ]


def _contracts_for_agents(
    derived: dict[str, Any],
    agent_ids: set[str],
    *,
    active: bool,
) -> list[dict[str, Any]]:
    key = "active_contracts" if active else "satisfied_contracts"
    return [
        contract for contract in derived["derived"][key]
        if contract.get("owner") in agent_ids
    ]


def render_surface_section(
    title: str,
    bundle: dict[str, Any],
    derived: dict[str, Any],
    surface: str,
) -> list[str]:
    lines = [title, ""]
    agents = _surface_agents(bundle, surface)
    agent_ids = {agent["id"] for agent in agents}
    labels = _agent_labels(bundle)

    lines.append("Agents")
    for agent in agents:
        lines.append(f"  - {agent['label']} ({agent['role']})")
    lines.append("")

    objectives = _objectives_for_surface(derived, surface)
    lines.append("Objectives")
    if objectives:
        for objective in objectives:
            lines.append(
                f"  - [{objective['state']}] {objective['label']} "
                f"({labels.get(objective['owner'], objective['owner'])})"
            )
    else:
        lines.append("  - none")
    lines.append("")

    active_contracts = _contracts_for_agents(derived, agent_ids, active=True)
    satisfied_contracts = _contracts_for_agents(derived, agent_ids, active=False)
    lines.append("Contracts")
    for contract in active_contracts:
        blocked = "blocked" if not contract.get("dependencies_satisfied") else "ready"
        lines.append(f"  - [active/{blocked}] {contract['id']}")
    for contract in satisfied_contracts:
        lines.append(f"  - [satisfied] {contract['id']}")
    if not active_contracts and not satisfied_contracts:
        lines.append("  - none")
    lines.append("")

    blocked = [
        item for item in derived["derived"]["blocked_executors"]
        if item["agent_id"] in agent_ids
    ]
    unblocked = [
        item for item in derived["derived"]["unblocked_executors"]
        if item["agent_id"] in agent_ids
    ]
    lines.append("Executor state")
    for item in blocked:
        lines.append(f"  - blocked: {item['agent_label']}")
    for item in unblocked:
        lines.append(f"  - unblocked: {item['agent_label']}")
    if not blocked and not unblocked:
        lines.append("  - none")
    lines.append("")

    submitted = [
        artifact for artifact in derived["derived"]["submitted_artifacts"]
        if artifact.get("producer") in agent_ids
    ]
    validations = derived["derived"]["validations_required"]
    artifact_to_contract = {
        validation["artifact"]: validation
        for validation in validations
    }
    lines.append("Artifacts")
    for artifact in submitted:
        lines.append(f"  - {artifact['id']} ({artifact['status']})")
    missing_active = [
        contract["artifact"]
        for contract in active_contracts
        if contract["artifact"] not in {item["id"] for item in submitted}
    ]
    for artifact_id in missing_active:
        lines.append(f"  - {artifact_id} (expected_missing)")
    if not submitted and not missing_active:
        lines.append("  - none")
    lines.append("")

    lines.append("Validations required")
    surface_validations = [
        validation for validation in validations
        if validation.get("contract") in {contract["id"] for contract in active_contracts + satisfied_contracts}
        or validation["artifact"] in {artifact["id"] for artifact in submitted}
    ]
    if surface_validations:
        for validation in surface_validations:
            lines.append(f"  - {validation['label']} ({validation['artifact']})")
    else:
        lines.append("  - none")
    lines.append("")
    return lines


def render(bundle: dict[str, Any], derived: dict[str, Any]) -> str:
    """Render Coordinate, Implement, and Value surfaces from derived state."""
    project = bundle.get("project", {})
    lines = [
        project.get("name", "Corus v1 Self-Build"),
        "",
        f"Active objectives: {len(derived['derived']['active_objectives'])}",
        f"Satisfied objectives: {len(derived['derived']['satisfied_objectives'])}",
        "",
    ]

    lines.extend(render_surface_section("Coordinate surface", bundle, derived, "coordinate"))
    lines.extend(render_surface_section("Implement surface", bundle, derived, "implement"))
    lines.extend(render_surface_section("Value surface", bundle, derived, "value"))

    return "\n".join(lines).strip() + "\n"
