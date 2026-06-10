"""Deterministic reducer for Corus v1 agent coordination state."""

from __future__ import annotations

from typing import Any

from corus_v1.load import index_by_id

OUTPUT_STATE_BY_ARTIFACT_STATUS = {
    "expected_missing": "missing",
    "present": "submitted",
    "validated": "satisfied",
    "rejected": "rejected",
}


def artifacts_by_id(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(bundle.get("artifacts", {}).get("artifacts", []))


def derive_readiness(contract: dict[str, Any], artifacts: dict[str, dict[str, Any]]) -> str:
    """Readiness reducer over required artifacts only."""
    required = contract.get("requires", [])
    if all(artifacts[artifact_id]["status"] == "validated" for artifact_id in required):
        return "unblocked"
    return "blocked"


def derive_output_state(contract: dict[str, Any], artifacts: dict[str, dict[str, Any]]) -> str:
    """Output reducer over the produced artifact only."""
    status = artifacts[contract["produces"]]["status"]
    return OUTPUT_STATE_BY_ARTIFACT_STATUS[str(status)]


def derive_contract_state(
    contract: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Contract state = readiness over requires + output over produces."""
    return {
        "id": contract["id"],
        "readiness": derive_readiness(contract, artifacts),
        "output": derive_output_state(contract, artifacts),
        "owner": contract["owner"],
        "executor": contract["executor"],
        "consumer": contract["consumer"],
        "requires": list(contract.get("requires", [])),
        "produces": contract["produces"],
        "objective": contract.get("objective"),
    }


def derive_contract_states(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = artifacts_by_id(bundle)
    contracts = bundle.get("contracts", {}).get("contracts", [])
    return [derive_contract_state(contract, artifacts) for contract in contracts]


def _objective_lists(
    objectives: list[dict[str, Any]],
    contract_states: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    states_by_id = {state["id"]: state for state in contract_states}
    active: list[dict[str, Any]] = []
    satisfied: list[dict[str, Any]] = []

    for objective in objectives:
        contract_ids = objective.get("contracts", [])
        outputs = [
            states_by_id[contract_id]["output"]
            for contract_id in contract_ids
            if contract_id in states_by_id
        ]
        entry = {
            "id": objective["id"],
            "intent": objective.get("intent"),
            "contracts": contract_ids,
        }
        if outputs and all(output == "satisfied" for output in outputs):
            satisfied.append(entry)
        else:
            active.append(entry)

    return active, satisfied


def derive_convenience_lists(contract_states: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Convenience lists derived from contract state vectors."""
    return {
        "blocked_contracts": [
            state["id"] for state in contract_states if state["readiness"] == "blocked"
        ],
        "unblocked_contracts": [
            state["id"] for state in contract_states if state["readiness"] == "unblocked"
        ],
        "submitted_contracts": [
            state["id"] for state in contract_states if state["output"] == "submitted"
        ],
        "satisfied_contracts": [
            state["id"] for state in contract_states if state["output"] == "satisfied"
        ],
        "rejected_contracts": [
            state["id"] for state in contract_states if state["output"] == "rejected"
        ],
    }


def derive(bundle: dict[str, Any]) -> dict[str, Any]:
    """Derive coordination state from declared objects."""
    contract_states = derive_contract_states(bundle)
    convenience = derive_convenience_lists(contract_states)
    objectives = bundle.get("objectives", {}).get("objectives", [])
    active_objectives, satisfied_objectives = _objective_lists(objectives, contract_states)

    return {
        "project": bundle.get("project", {}),
        "derived": {
            "contract_states": contract_states,
            **convenience,
            "active_objectives": active_objectives,
            "satisfied_objectives": satisfied_objectives,
        },
    }


def with_artifact_status(
    bundle: dict[str, Any],
    artifact_id: str,
    status: str,
) -> dict[str, Any]:
    """Return a copy of bundle with one artifact status changed."""
    import copy

    updated = copy.deepcopy(bundle)
    for artifact in updated.get("artifacts", {}).get("artifacts", []):
        if artifact["id"] == artifact_id:
            artifact["status"] = status
            break
    return updated
