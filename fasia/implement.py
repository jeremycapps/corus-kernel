"""Executor-relation Fasia packet projection."""

from __future__ import annotations

from typing import Any

from fasia.types import (
    contract_states_by_id,
    produced_artifacts,
    submit_action_id,
)


def derive_implement_packet(
    flow: dict[str, Any],
    executor_id: str,
    contracts: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Project coordination flow for one executor relation."""
    del artifacts
    states_by_id = contract_states_by_id(flow)
    selected_contracts = sorted(
        [
            contract
            for contract in contracts
            if contract.get("executor") == executor_id
        ],
        key=lambda item: item["id"],
    )
    selected_ids = [contract["id"] for contract in selected_contracts]
    states = [
        states_by_id[contract_id]
        for contract_id in selected_ids
        if contract_id in states_by_id
    ]

    ready = sorted(
        state["id"]
        for state in states
        if state["readiness"] == "unblocked" and state["output"] in {"missing", "rejected"}
    )
    blocked = sorted(state["id"] for state in states if state["readiness"] == "blocked")
    blocked_by = {
        state["id"]: list(state.get("blocked_by", []))
        for state in states
        if state.get("blocked_by")
    }
    producible = {
        state["id"]: produced_artifacts(state)
        for state in states
        if state["id"] in ready
    }
    unavailable = sorted(
        state["id"]
        for state in states
        if state["id"] not in ready
    )

    return {
        "packet": {
            "id": "packet.implement",
            "type": "implement",
            "relation": "executor",
            "actor": executor_id,
        },
        "queues": {
            "ready_to_execute": ready,
            "blocked": blocked,
        },
        "blocked_by": blocked_by,
        "producible": producible,
        "produced_artifacts": {
            state["id"]: produced_artifacts(state)
            for state in states
        },
        "actions": {
            "available": [
                submit_action_id(artifact_id)
                for state in states
                if state["id"] in ready
                for artifact_id in produced_artifacts(state)
            ],
            "unavailable": [
                submit_action_id(artifact_id)
                for state in states
                if state["id"] in unavailable
                for artifact_id in produced_artifacts(state)
            ],
        },
        "work_packets": [
            {
                "contract": state["id"],
                "produces": produced_artifacts(state),
                "readiness": state["readiness"],
                "output": state["output"],
            }
            for state in states
        ],
        "trace": {
            "derived_from": selected_ids,
        },
    }
