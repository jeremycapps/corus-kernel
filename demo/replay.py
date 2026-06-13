"""Replay demo events around the deterministic Corus v1 kernel.

The demo layer owns source refs, claims, and surfaces. The kernel owns
coordination flow. This module only mutates copied wrapper state before calling
``corus_v1.derive``.
"""

from __future__ import annotations

import copy
from typing import Any

from corus_v1.derive import derive

CLAIM_STATUSES = frozenset({
    "candidate",
    "supported",
    "admitted",
    "rejected",
    "missing_evidence",
})


def _artifact_items(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return bundle.get("artifacts", {}).get("artifacts", [])


def _artifact_statuses(bundle: dict[str, Any]) -> dict[str, str]:
    return {
        artifact["id"]: artifact["status"]
        for artifact in sorted(_artifact_items(bundle), key=lambda item: item["id"])
    }


def _claim_map(claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {claim["id"]: claim for claim in claims}


def _sorted_values(items_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [items_by_id[item_id] for item_id in sorted(items_by_id)]


def _next_contract_ids(actions: list[dict[str, Any]]) -> list[str]:
    return [action["contract"] for action in actions]


def _make_state(
    bundle: dict[str, Any],
    *,
    claims: list[dict[str, Any]] | None = None,
    source_refs: list[dict[str, Any]] | None = None,
    event_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "bundle": copy.deepcopy(bundle),
        "claims": list(copy.deepcopy(claims or [])),
        "source_refs": list(copy.deepcopy(source_refs or [])),
        "event_log": list(copy.deepcopy(event_log or [])),
    }


def _set_artifact_status(state: dict[str, Any], event: dict[str, Any]) -> None:
    artifact_id = event["artifact"]
    status = event["status"]
    for artifact in _artifact_items(state["bundle"]):
        if artifact["id"] == artifact_id:
            artifact["status"] = status
            return
    raise ValueError(f"Unknown artifact: {artifact_id}")


def _set_claim_status(state: dict[str, Any], event: dict[str, Any]) -> None:
    claim_id = event["claim"]
    status = event["status"]
    if status not in CLAIM_STATUSES:
        raise ValueError(f"Invalid claim status: {status}")

    claims = _claim_map(state["claims"])
    claim = claims.get(claim_id, {"id": claim_id})
    claim["status"] = status

    for field in ("text", "artifact", "source_refs", "evidence_refs"):
        if field in event:
            claim[field] = copy.deepcopy(event[field])

    claims[claim_id] = claim
    state["claims"] = _sorted_values(claims)


def _add_source_ref(state: dict[str, Any], event: dict[str, Any]) -> None:
    source_id = event["source"]
    source_refs = {item["id"]: item for item in state["source_refs"]}
    source_refs[source_id] = {
        "id": source_id,
        "label": event.get("label", source_id),
        "locator": event.get("locator"),
    }
    state["source_refs"] = _sorted_values(source_refs)


def apply_event(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Apply one demo event to wrapper state and return a new state."""
    next_state = _make_state(
        state["bundle"],
        claims=state.get("claims", []),
        source_refs=state.get("source_refs", []),
        event_log=state.get("event_log", []),
    )
    event_type = event["type"]

    if event_type in {"context_opened", "next_work_derived"}:
        pass
    elif event_type == "artifact_status_set":
        _set_artifact_status(next_state, event)
    elif event_type == "claim_status_set":
        _set_claim_status(next_state, event)
    elif event_type == "source_ref_added":
        _add_source_ref(next_state, event)
    else:
        raise ValueError(f"Unknown replay event type: {event_type}")

    next_state["event_log"].append(copy.deepcopy(event))
    return next_state


def render_demo_payloads(
    state: dict[str, Any],
    kernel_output: dict[str, Any],
) -> dict[str, Any]:
    """Render Coordinate, Implement, and Value payloads from replay state."""
    derived = kernel_output["derived"]
    artifact_statuses = _artifact_statuses(state["bundle"])
    claims = list(state.get("claims", []))
    rejected_claims = [
        claim for claim in claims if claim.get("status") == "rejected"
    ]
    admitted_claims = [
        claim for claim in claims if claim.get("status") == "admitted"
    ]
    unresolved_claims = [
        claim
        for claim in claims
        if claim.get("status") in {"candidate", "missing_evidence"}
    ]

    next_work = derived["next_work"]
    return {
        "coordinate": {
            "surface": "Coordinate",
            "role": "owner",
            "objectives": derived["objectives"],
            "artifact_statuses": artifact_statuses,
            "blocked_contracts": derived["blocked_contracts"],
            "unblocked_contracts": derived["unblocked_contracts"],
            "next_executor_actions": _next_contract_ids(next_work["executor_actions"]),
            "next_consumer_actions": _next_contract_ids(next_work["consumer_actions"]),
            "rejected_claims": rejected_claims,
            "event_count": len(state.get("event_log", [])),
        },
        "implement": {
            "surface": "Implement",
            "role": "executor",
            "executor_actions": next_work["executor_actions"],
            "blocked_contracts": derived["blocked_contracts"],
            "artifact_statuses": artifact_statuses,
            "source_refs": list(state.get("source_refs", [])),
            "unresolved_claims": unresolved_claims,
        },
        "value": {
            "surface": "Value",
            "role": "consumer",
            "consumer_actions": next_work["consumer_actions"],
            "submitted_contracts": derived["submitted_contracts"],
            "satisfied_contracts": derived["satisfied_contracts"],
            "admitted_claims": admitted_claims,
            "rejected_claims": rejected_claims,
            "source_refs": list(state.get("source_refs", [])),
        },
    }


def apply_replay(
    bundle: dict[str, Any],
    events: list[dict[str, Any]],
    *,
    claims: list[dict[str, Any]] | None = None,
    source_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Apply demo events, call the kernel reducer, and render demo surfaces."""
    state = _make_state(bundle, claims=claims, source_refs=source_refs)
    for event in events:
        state = apply_event(state, event)

    kernel_output = derive(state["bundle"])
    return {
        "state": {
            "claims": state["claims"],
            "source_refs": state["source_refs"],
            "event_log": state["event_log"],
            "artifact_statuses": _artifact_statuses(state["bundle"]),
        },
        "kernel": kernel_output,
        "surfaces": render_demo_payloads(state, kernel_output),
    }
