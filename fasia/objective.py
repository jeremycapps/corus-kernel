"""Objective-scope work packet projection."""

from __future__ import annotations

from typing import Any

from fasia.types import contract_states_by_id, objective_states_by_id


def derive_objective_surface(
    flow: dict[str, Any],
    objective: dict[str, Any],
    contracts: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Project coordination flow over one objective scope."""
    del contracts, artifacts
    states_by_id = contract_states_by_id(flow)
    objective_state = objective_states_by_id(flow).get(objective["id"], {})
    contract_ids = sorted(objective.get("contracts", []))
    states = [
        states_by_id[contract_id]
        for contract_id in contract_ids
        if contract_id in states_by_id
    ]

    blocked = sorted(state["id"] for state in states if state["readiness"] == "blocked")
    unblocked = sorted(state["id"] for state in states if state["readiness"] == "unblocked")
    submitted = sorted(state["id"] for state in states if state["output"] == "submitted")
    satisfied = sorted(state["id"] for state in states if state["output"] == "satisfied")
    rejected = sorted(state["id"] for state in states if state["output"] == "rejected")
    missing_artifacts = sorted(
        artifact_id
        for state in states
        if state["output"] == "missing"
        for artifact_id in state.get("produces", [])
    )
    bottlenecks = sorted({
        artifact_id
        for state in states
        for artifact_id in state.get("blocked_by", [])
    })

    executor_actions = flow.get("next_work", {}).get("executor_actions", [])
    consumer_actions = flow.get("next_work", {}).get("consumer_actions", [])
    required_execution = sorted({
        artifact_id
        for action in executor_actions
        if action["contract"] in contract_ids
        for artifact_id in action.get("produces", [])
    })
    required_validation = sorted({
        artifact_id
        for action in consumer_actions
        if action["contract"] in contract_ids
        for artifact_id in action.get("produces", [])
    })

    return {
        "surface": {
            "id": "surface.objective",
            "type": "objective",
            "relation": "objective_scope",
            "subject": objective["id"],
        },
        "summary": {
            "objective_state": (
                "satisfied" if objective_state.get("satisfied") else "unsatisfied"
            ),
            "contracts_total": len(contract_ids),
            "contracts_blocked": len(blocked),
            "contracts_unblocked": len(unblocked),
            "contracts_submitted": len(submitted),
            "contracts_satisfied": len(satisfied),
            "contracts_rejected": len(rejected),
        },
        "queues": {
            "blocked": blocked,
            "unblocked": unblocked,
            "needs_validation": submitted,
            "satisfied": satisfied,
            "rejected": rejected,
        },
        "missing_artifacts": missing_artifacts,
        "bottlenecks": bottlenecks,
        "next": {
            "required_validation": required_validation,
            "required_execution": required_execution,
        },
        "trace": {
            "derived_from": [
                objective["id"],
                "contracts",
                "artifacts",
                "flow",
            ],
        },
    }
