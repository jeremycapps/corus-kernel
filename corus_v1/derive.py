"""Deterministic reducer for Corus v1 coordination flow."""

from __future__ import annotations

import copy
from typing import Any

from corus_v1.load import index_by_id

ARTIFACT_STATUSES = frozenset({
    "expected_missing",
    "present",
    "validated",
    "rejected",
})


class DeclarationValidationError(Exception):
    """Raised when declared Corus objects fail validation."""

    def __init__(self, errors: list[dict[str, Any]]):
        self.errors = errors
        message = "; ".join(error["message"] for error in errors)
        super().__init__(message)


def _items(bundle: dict[str, Any], collection: str) -> list[dict[str, Any]]:
    return list(bundle.get(collection, {}).get(collection, []))


def agents_by_id(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(_items(bundle, "agents"))


def objectives_by_id(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(_items(bundle, "objectives"))


def artifacts_by_id(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(_items(bundle, "artifacts"))


def contracts_by_id(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(_items(bundle, "contracts"))


def _add_error(
    errors: list[dict[str, Any]],
    code: str,
    message: str,
    **detail: Any,
) -> None:
    errors.append({"code": code, "message": message, **detail})


def _validate_unique_ids(bundle: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    seen: dict[str, str] = {}
    for collection in ("agents", "objectives", "contracts", "artifacts"):
        local: set[str] = set()
        for item in _items(bundle, collection):
            item_id = item.get("id")
            if not item_id:
                _add_error(
                    errors,
                    "missing_id",
                    f"{collection} item is missing id",
                    collection=collection,
                )
                continue
            if item_id in local:
                _add_error(
                    errors,
                    "duplicate_id",
                    f"{collection}: duplicate id {item_id}",
                    collection=collection,
                    item_id=item_id,
                )
            local.add(item_id)
            if item_id in seen:
                _add_error(
                    errors,
                    "duplicate_id",
                    f"duplicate id {item_id} in {collection} and {seen[item_id]}",
                    collection=collection,
                    item_id=item_id,
                )
            else:
                seen[item_id] = collection


def _validate_artifact_graph(
    artifacts: dict[str, dict[str, Any]],
    errors: list[dict[str, Any]],
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(artifact_id: str, path: list[str]) -> None:
        if artifact_id in visited:
            return
        if artifact_id in visiting:
            cycle_start = path.index(artifact_id)
            cycle = path[cycle_start:] + [artifact_id]
            _add_error(
                errors,
                "artifact_dependency_cycle",
                f"artifact dependency cycle: {' -> '.join(cycle)}",
                artifact_id=artifact_id,
                cycle=cycle,
            )
            return

        visiting.add(artifact_id)
        artifact = artifacts[artifact_id]
        for required_id in artifact.get("requires", []):
            if required_id in artifacts:
                visit(required_id, path + [required_id])
        visiting.remove(artifact_id)
        visited.add(artifact_id)

    for artifact_id in sorted(artifacts):
        visit(artifact_id, [artifact_id])


def validate_declared_objects(bundle: dict[str, Any]) -> None:
    """Validate declarations before deriving flow."""
    errors: list[dict[str, Any]] = []
    _validate_unique_ids(bundle, errors)

    agents = agents_by_id(bundle)
    objectives = objectives_by_id(bundle)
    contracts = contracts_by_id(bundle)
    artifacts = artifacts_by_id(bundle)

    for objective in objectives.values():
        objective_id = objective["id"]
        for agent_id in objective.get("agents", []):
            if agent_id not in agents:
                _add_error(
                    errors,
                    "missing_objective_agent",
                    f"objective {objective_id}: agent {agent_id} not found",
                    objective_id=objective_id,
                    agent_id=agent_id,
                )
        objective_agents = set(objective.get("agents", []))
        for contract_id in objective.get("contracts", []):
            contract = contracts.get(contract_id)
            if contract is None:
                _add_error(
                    errors,
                    "missing_objective_contract",
                    f"objective {objective_id}: contract {contract_id} not found",
                    objective_id=objective_id,
                    contract_id=contract_id,
                )
                continue
            for role in ("executor", "consumer"):
                agent_id = contract.get(role)
                if agent_id not in objective_agents:
                    _add_error(
                        errors,
                        "contract_agent_not_in_objective",
                        f"objective {objective_id}: contract {contract_id} {role} "
                        f"{agent_id} is not in objective agents",
                        objective_id=objective_id,
                        contract_id=contract_id,
                        agent_id=agent_id,
                        role=role,
                    )

        producer_counts: dict[str, list[str]] = {}
        for contract_id in objective.get("contracts", []):
            contract = contracts.get(contract_id)
            if contract is None:
                continue
            for artifact_id in contract.get("produces", []):
                producer_counts.setdefault(artifact_id, []).append(contract_id)
        for artifact_id, producer_ids in sorted(producer_counts.items()):
            if len(producer_ids) > 1:
                _add_error(
                    errors,
                    "duplicate_artifact_producer",
                    f"objective {objective_id}: artifact {artifact_id} produced by "
                    f"multiple contracts {producer_ids}",
                    objective_id=objective_id,
                    artifact_id=artifact_id,
                    contract_ids=producer_ids,
                )

    for contract in contracts.values():
        contract_id = contract["id"]
        executor = contract.get("executor")
        consumer = contract.get("consumer")
        if executor not in agents:
            _add_error(
                errors,
                "missing_contract_executor",
                f"contract {contract_id}: executor {executor} not found",
                contract_id=contract_id,
                agent_id=executor,
            )
        if consumer not in agents:
            _add_error(
                errors,
                "missing_contract_consumer",
                f"contract {contract_id}: consumer {consumer} not found",
                contract_id=contract_id,
                agent_id=consumer,
            )
        if executor == consumer:
            _add_error(
                errors,
                "contract_self_consumer",
                f"contract {contract_id}: executor and consumer must differ",
                contract_id=contract_id,
                agent_id=executor,
            )
        produces = contract.get("produces")
        if not isinstance(produces, list) or not produces:
            _add_error(
                errors,
                "invalid_contract_produces",
                f"contract {contract_id}: produces must be a non-empty list",
                contract_id=contract_id,
            )
            continue
        for artifact_id in produces:
            if artifact_id not in artifacts:
                _add_error(
                    errors,
                    "missing_contract_artifact",
                    f"contract {contract_id}: produced artifact {artifact_id} not found",
                    contract_id=contract_id,
                    artifact_id=artifact_id,
                )

    for artifact in artifacts.values():
        artifact_id = artifact["id"]
        status = artifact.get("status")
        if status not in ARTIFACT_STATUSES:
            _add_error(
                errors,
                "invalid_artifact_status",
                f"artifact {artifact_id}: invalid status {status!r}",
                artifact_id=artifact_id,
                status=status,
            )
        requires = artifact.get("requires")
        if not isinstance(requires, list):
            _add_error(
                errors,
                "invalid_artifact_requires",
                f"artifact {artifact_id}: requires must be a list",
                artifact_id=artifact_id,
            )
            continue
        for required_id in requires:
            if required_id not in artifacts:
                _add_error(
                    errors,
                    "missing_artifact_requirement",
                    f"artifact {artifact_id}: required artifact {required_id} not found",
                    artifact_id=artifact_id,
                    required_id=required_id,
                )

    _validate_artifact_graph(artifacts, errors)

    if errors:
        raise DeclarationValidationError(errors)


def derive_contract_readiness(
    contract: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Derive readiness from direct requirements of produced artifacts."""
    blocked_by: list[str] = []
    produced = sorted(contract.get("produces", []))
    for artifact_id in produced:
        artifact = artifacts[artifact_id]
        for required_id in sorted(artifact.get("requires", [])):
            if artifacts[required_id]["status"] != "validated":
                blocked_by.append(required_id)

    blocked_by = sorted(set(blocked_by))
    readiness = "unblocked" if not blocked_by else "blocked"
    reason = (
        "all requirements validated"
        if readiness == "unblocked"
        else "missing or unvalidated requirements"
    )
    return {
        "readiness": readiness,
        "blocked_by": blocked_by,
        "readiness_reason": reason,
    }


def derive_contract_output(
    contract: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Derive output state from statuses of produced artifacts."""
    produced = sorted(contract.get("produces", []))
    statuses = [artifacts[artifact_id]["status"] for artifact_id in produced]
    current_statuses = {
        artifact_id: artifacts[artifact_id]["status"] for artifact_id in produced
    }

    if any(status == "rejected" for status in statuses):
        output = "rejected"
        reason = "at least one produced artifact is rejected"
    elif all(status == "validated" for status in statuses):
        output = "satisfied"
        reason = "all produced artifacts are validated"
    elif all(status == "expected_missing" for status in statuses):
        output = "missing"
        reason = "all produced artifacts are expected_missing"
    elif all(status == "present" for status in statuses):
        output = "submitted"
        reason = "all produced artifacts are present"
    else:
        output = "partial"
        reason = "produced artifact statuses are mixed"

    return {
        "output": output,
        "artifact_statuses": current_statuses,
        "output_reason": reason,
        "rejected_artifacts": [
            artifact_id
            for artifact_id, status in current_statuses.items()
            if status == "rejected"
        ],
    }


def derive_contract_state(
    contract: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    readiness = derive_contract_readiness(contract, artifacts)
    output = derive_contract_output(contract, artifacts)
    return {
        "id": contract["id"],
        "readiness": readiness["readiness"],
        "output": output["output"],
        "executor": contract["executor"],
        "consumer": contract["consumer"],
        "produces": sorted(contract["produces"]),
        "artifact_statuses": output["artifact_statuses"],
        "blocked_by": readiness["blocked_by"],
        "rejected_artifacts": output["rejected_artifacts"],
        "trace": {
            "contract": contract["id"],
            "produced_artifacts": sorted(contract["produces"]),
            "readiness": readiness["readiness_reason"],
            "output": output["output_reason"],
        },
    }


def derive_contract_states(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = artifacts_by_id(bundle)
    return [
        derive_contract_state(contract, artifacts)
        for contract in sorted(_items(bundle, "contracts"), key=lambda item: item["id"])
    ]


def derive_objective_state(
    objective: dict[str, Any],
    contract_states_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    contract_ids = sorted(objective.get("contracts", []))
    preventing = [
        contract_id
        for contract_id in contract_ids
        if contract_states_by_id[contract_id]["output"] != "satisfied"
    ]
    return {
        "id": objective["id"],
        "intent": objective.get("intent"),
        "agents": sorted(objective.get("agents", [])),
        "contracts": contract_ids,
        "satisfied": not preventing,
        "prevented_by": preventing,
        "trace": {
            "satisfaction": (
                "all listed contracts are satisfied"
                if not preventing
                else "listed contracts are not all satisfied"
            ),
            "prevented_by": preventing,
        },
    }


def _next_action(
    state: dict[str, Any],
    why: str,
) -> dict[str, Any]:
    return {
        "contract": state["id"],
        "executor": state["executor"],
        "consumer": state["consumer"],
        "produces": state["produces"],
        "artifact_statuses": state["artifact_statuses"],
        "why": why,
    }


def derive_next_work(contract_states: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    executor_actions: list[dict[str, Any]] = []
    consumer_actions: list[dict[str, Any]] = []

    for state in sorted(contract_states, key=lambda item: item["id"]):
        if state["readiness"] != "unblocked":
            continue
        if state["output"] in {"missing", "rejected"}:
            executor_actions.append(
                _next_action(
                    state,
                    "contract is unblocked and needs executor action",
                )
            )
        elif state["output"] == "submitted":
            consumer_actions.append(
                _next_action(
                    state,
                    "contract is submitted and needs consumer validation",
                )
            )

    return {
        "executor_actions": executor_actions,
        "consumer_actions": consumer_actions,
    }


def _bucket(contract_states: list[dict[str, Any]], key: str, value: str) -> list[str]:
    return sorted(state["id"] for state in contract_states if state[key] == value)


def derive_flow(bundle: dict[str, Any]) -> dict[str, Any]:
    """Derive deterministic coordination flow from declared objects."""
    validate_declared_objects(bundle)
    contract_states = derive_contract_states(bundle)
    contract_states_by_id = {state["id"]: state for state in contract_states}
    objective_states = [
        derive_objective_state(objective, contract_states_by_id)
        for objective in sorted(_items(bundle, "objectives"), key=lambda item: item["id"])
    ]
    next_work = derive_next_work(contract_states)

    return {
        "derived": {
            "objectives": objective_states,
            "contracts": contract_states,
            "blocked_contracts": _bucket(contract_states, "readiness", "blocked"),
            "unblocked_contracts": _bucket(contract_states, "readiness", "unblocked"),
            "submitted_contracts": _bucket(contract_states, "output", "submitted"),
            "satisfied_contracts": _bucket(contract_states, "output", "satisfied"),
            "rejected_contracts": _bucket(contract_states, "output", "rejected"),
            "partial_contracts": _bucket(contract_states, "output", "partial"),
            "missing_contracts": _bucket(contract_states, "output", "missing"),
            "next_work": next_work,
        },
    }


def derive(bundle: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper for the v1 reducer."""
    return derive_flow(bundle)


def with_artifact_status(
    bundle: dict[str, Any],
    artifact_id: str,
    status: str,
) -> dict[str, Any]:
    """Return a copy of bundle with one artifact status changed."""
    updated = copy.deepcopy(bundle)
    for artifact in updated.get("artifacts", {}).get("artifacts", []):
        if artifact["id"] == artifact_id:
            artifact["status"] = status
            break
    return updated
