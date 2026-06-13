"""Consumer-relation Fasia packet projection."""

from __future__ import annotations

from typing import Any

from fasia.types import (
    contract_states_by_id,
    produced_artifacts,
    reject_action_id,
    validate_action_id,
)


def derive_validate_packet(
    flow: dict[str, Any],
    consumer_id: str,
    contracts: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Project coordination flow for one consumer relation."""
    del artifacts
    states_by_id = contract_states_by_id(flow)
    selected_contracts = sorted(
        [
            contract
            for contract in contracts
            if contract.get("consumer") == consumer_id
        ],
        key=lambda item: item["id"],
    )
    selected_ids = [contract["id"] for contract in selected_contracts]
    states = [
        states_by_id[contract_id]
        for contract_id in selected_ids
        if contract_id in states_by_id
    ]
    needs_validation = [
        state for state in states if state["output"] == "submitted"
    ]
    accepted = [
        state for state in states if state["output"] == "satisfied"
    ]
    rejected = [
        state for state in states if state["output"] == "rejected"
    ]

    needs_validation_artifacts = sorted(
        artifact_id
        for state in needs_validation
        for artifact_id in produced_artifacts(state)
    )
    accepted_artifacts = sorted(
        artifact_id
        for state in accepted
        for artifact_id in produced_artifacts(state)
    )
    rejected_artifacts = sorted(
        artifact_id
        for state in rejected
        for artifact_id in produced_artifacts(state)
    )

    return {
        "packet": {
            "id": "packet.validate",
            "type": "validate",
            "relation": "consumer",
            "actor": consumer_id,
        },
        "queues": {
            "needs_validation": needs_validation_artifacts,
            "accepted": accepted_artifacts,
            "rejected": rejected_artifacts,
        },
        "contracts": {
            "needs_validation": sorted(state["id"] for state in needs_validation),
            "satisfied": sorted(state["id"] for state in accepted),
            "rejected": sorted(state["id"] for state in rejected),
        },
        "submitted_work": needs_validation_artifacts,
        "actions": {
            "available": [
                action_id
                for artifact_id in needs_validation_artifacts
                for action_id in (
                    validate_action_id(artifact_id),
                    reject_action_id(artifact_id),
                )
            ],
        },
        "downstream": {
            "blocked_objectives": [
                objective["id"]
                for objective in flow.get("objectives", [])
                for state in needs_validation
                if state["id"] in objective.get("prevented_by", [])
            ],
        },
        "trace": {
            "derived_from": selected_ids + needs_validation_artifacts,
        },
    }
