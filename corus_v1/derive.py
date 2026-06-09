"""Deterministic reducer for Corus v1 self-build state."""

from __future__ import annotations

from typing import Any

from corus_v1.load import index_by_id

SUBMITTED_STATUSES = frozenset({"present", "validated"})
SATISFIED_CONTRACT_STATUSES = frozenset({"validated"})
VALIDATION_REQUIRED_STATUSES = frozenset({"present"})


def artifact_status(bundle: dict[str, Any], artifact_id: str) -> str:
    artifacts = index_by_id(bundle.get("artifacts", {}).get("artifacts", []))
    artifact = artifacts.get(artifact_id)
    if artifact is None:
        return "expected_missing"
    return str(artifact.get("status", "expected_missing"))


def dependencies_satisfied(bundle: dict[str, Any], depends_on: list[str] | None) -> bool:
    if not depends_on:
        return True
    return all(
        artifact_status(bundle, artifact_id) == "validated"
        for artifact_id in depends_on
    )


def contract_satisfied(bundle: dict[str, Any], contract: dict[str, Any]) -> bool:
    return artifact_status(bundle, contract["artifact"]) in SATISFIED_CONTRACT_STATUSES


def objective_satisfied(bundle: dict[str, Any], objective: dict[str, Any]) -> bool:
    contracts = index_by_id(bundle.get("contracts", {}).get("contracts", []))
    for contract_id in objective.get("contracts", []):
        contract = contracts.get(contract_id)
        if contract is None or not contract_satisfied(bundle, contract):
            return False
    return True


def validation_satisfied(bundle: dict[str, Any], validation: dict[str, Any]) -> bool:
    required = validation.get("required_status", "validated")
    status = artifact_status(bundle, validation["artifact"])
    if required == "validated":
        return status == "validated"
    return status in SUBMITTED_STATUSES


def derive_active_contracts(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    contracts = bundle.get("contracts", {}).get("contracts", [])
    active: list[dict[str, Any]] = []
    for contract in contracts:
        if not contract_satisfied(bundle, contract):
            active.append({
                "id": contract["id"],
                "owner": contract["owner"],
                "artifact": contract["artifact"],
                "objective": contract.get("objective"),
                "depends_on": contract.get("depends_on", []),
                "dependencies_satisfied": dependencies_satisfied(
                    bundle, contract.get("depends_on")
                ),
            })
    return active


def derive_satisfied_contracts(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    contracts = bundle.get("contracts", {}).get("contracts", [])
    return [
        {
            "id": contract["id"],
            "owner": contract["owner"],
            "artifact": contract["artifact"],
            "artifact_status": artifact_status(bundle, contract["artifact"]),
        }
        for contract in contracts
        if contract_satisfied(bundle, contract)
    ]


def derive_active_objectives(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    objectives = bundle.get("objectives", {}).get("objectives", [])
    return [
        {
            "id": objective["id"],
            "label": objective["label"],
            "owner": objective["owner"],
            "surface": objective.get("surface"),
            "contracts": objective.get("contracts", []),
        }
        for objective in objectives
        if not objective_satisfied(bundle, objective)
    ]


def derive_satisfied_objectives(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    objectives = bundle.get("objectives", {}).get("objectives", [])
    return [
        {
            "id": objective["id"],
            "label": objective["label"],
            "owner": objective["owner"],
            "surface": objective.get("surface"),
        }
        for objective in objectives
        if objective_satisfied(bundle, objective)
    ]


def derive_submitted_artifacts(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = bundle.get("artifacts", {}).get("artifacts", [])
    return [
        {
            "id": artifact["id"],
            "label": artifact["label"],
            "status": artifact["status"],
            "producer": artifact.get("producer"),
        }
        for artifact in artifacts
        if artifact.get("status") in SUBMITTED_STATUSES
    ]


def derive_validations_required(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    validations = bundle.get("validations", {}).get("validations", [])
    required: list[dict[str, Any]] = []
    for validation in validations:
        if validation_satisfied(bundle, validation):
            continue
        status = artifact_status(bundle, validation["artifact"])
        if status in VALIDATION_REQUIRED_STATUSES:
            required.append({
                "id": validation["id"],
                "label": validation["label"],
                "artifact": validation["artifact"],
                "contract": validation.get("contract"),
                "artifact_status": status,
                "required_status": validation.get("required_status", "validated"),
            })
    return required


def derive_executor_state(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    agents = index_by_id(bundle.get("agents", {}).get("agents", []))
    active_contracts = derive_active_contracts(bundle)
    blocked: list[dict[str, Any]] = []
    unblocked: list[dict[str, Any]] = []

    contracts_by_owner: dict[str, list[dict[str, Any]]] = {}
    for contract in active_contracts:
        contracts_by_owner.setdefault(contract["owner"], []).append(contract)

    for owner_id, owner_contracts in sorted(contracts_by_owner.items()):
        agent = agents.get(owner_id, {"id": owner_id, "label": owner_id})
        deps_ok = all(contract["dependencies_satisfied"] for contract in owner_contracts)
        entry = {
            "agent_id": owner_id,
            "agent_label": agent.get("label", owner_id),
            "surface": agent.get("surface"),
            "role": agent.get("role"),
            "active_contracts": [contract["id"] for contract in owner_contracts],
        }
        if deps_ok:
            unblocked.append(entry)
        else:
            blocked.append(entry)

    return blocked, unblocked


def derive(bundle: dict[str, Any]) -> dict[str, Any]:
    """Derive deterministic self-build state from a loaded project bundle."""
    blocked, unblocked = derive_executor_state(bundle)
    return {
        "project": bundle.get("project", {}),
        "derived": {
            "active_objectives": derive_active_objectives(bundle),
            "active_contracts": derive_active_contracts(bundle),
            "blocked_executors": blocked,
            "unblocked_executors": unblocked,
            "submitted_artifacts": derive_submitted_artifacts(bundle),
            "validations_required": derive_validations_required(bundle),
            "satisfied_contracts": derive_satisfied_contracts(bundle),
            "satisfied_objectives": derive_satisfied_objectives(bundle),
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
    artifacts = updated.get("artifacts", {}).get("artifacts", [])
    for artifact in artifacts:
        if artifact["id"] == artifact_id:
            artifact["status"] = status
            break
    return updated
