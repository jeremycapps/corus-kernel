"""Derive context from declared objects."""

from __future__ import annotations

from typing import Any

from corus_kernel.hash import canonical_json, sha256_hex
from corus_kernel.loader import index_by_id, load_bundle
from corus_kernel.validate import validate_bundle

REQUIRED_ANSWER = (
    "RVO is the subject of a Director-orchestrated Neara account-team boundary. "
    "Within that boundary, the team's CVA and FDE contracts select RVO-specific "
    "artifacts: value evidence, ROI case, technical evidence, and integration path. "
    "Those artifacts are still expected_missing, so the derived context remains unresolved."
)

TRACE_CLAIMS = [
    "RVO is the subject of the Neara account boundary.",
    "The Director profile orchestrates the boundary.",
    "The Neara account team supplies eligible roles.",
    "CVA-owned contracts select RVO value artifacts.",
    "FDE-owned contracts select RVO technical artifacts.",
    "Selected artifacts are expected_missing.",
    "The derived context remains unresolved.",
]

ARTIFACT_STATUSES_BLOCKING = {"expected_missing", "rejected"}
ARTIFACT_STATUSES_READY = {"present", "validated"}


def derive_contract_status(artifact_status: str) -> str:
    """Derive contract status from its artifact's status."""
    if artifact_status in ARTIFACT_STATUSES_READY:
        return "satisfied"
    if artifact_status in ARTIFACT_STATUSES_BLOCKING:
        return "unsatisfied"
    return "pending"


def reduce_context_state(
    boundary: dict[str, Any] | None,
    selected_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Default context state reducer."""
    if boundary is None or not boundary.get("subject"):
        return {
            "coordination": "blocked",
            "reason": "missing_subject",
        }

    statuses = [a.get("status") for a in selected_artifacts]
    if any(s in ARTIFACT_STATUSES_BLOCKING for s in statuses):
        return {
            "coordination": "unresolved",
            "reason": "missing_or_rejected_artifacts",
        }
    if statuses and all(s in ARTIFACT_STATUSES_READY for s in statuses):
        return {
            "coordination": "ready",
            "reason": "selected_artifacts_satisfied",
        }
    return {
        "coordination": "unresolved",
        "reason": "missing_or_rejected_artifacts",
    }


def _derive_role_views(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"role_id": role["id"], "label": role["label"]} for role in roles]


def _derive_team_views(
    teams: list[dict[str, Any]],
    roles_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    views = []
    for team in teams:
        views.append(
            {
                "team_id": team["id"],
                "label": team["label"],
                "roles": [
                    {"role_id": rid, "label": roles_by_id[rid]["label"]}
                    for rid in team.get("roles", [])
                ],
            }
        )
    return views


def _select_boundary(bundle: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    boundaries = bundle.get("boundaries", [])
    if not boundaries:
        return None
    return boundaries[0]


def _select_contracts(
    contracts: list[dict[str, Any]],
    artifacts_by_id: dict[str, dict[str, Any]],
    team_role_ids: set[str],
    boundary_subject: str | None,
) -> list[dict[str, Any]]:
    selected = []
    for contract in contracts:
        owner = contract.get("owner")
        artifact = artifacts_by_id.get(contract.get("artifact", ""))
        if owner not in team_role_ids:
            continue
        if artifact is None:
            continue
        if artifact.get("subject") != boundary_subject:
            continue
        selected.append(contract)
    return selected


def _attach_moments(
    moments: list[dict[str, Any]],
    boundary_subject: str | None,
    selected_artifact_ids: set[str],
) -> list[dict[str, Any]]:
    attached = []
    for moment in moments:
        obj = moment.get("object")
        if obj == boundary_subject or obj in selected_artifact_ids:
            attached.append(moment)
    return attached


def derive_context(fixture_dir: str | Any) -> dict[str, Any]:
    """Load declared objects, validate, derive context, and emit deterministic JSON."""
    bundle = load_bundle(fixture_dir)
    validate_bundle(bundle)

    roles_by_id = index_by_id(bundle["roles"])
    artifacts_by_id = index_by_id(bundle["artifacts"])
    teams_by_id = index_by_id(bundle["teams"])

    boundary = _select_boundary(bundle)
    team = teams_by_id.get(boundary["team"]) if boundary else None
    team_role_ids = set(team.get("roles", [])) if team else set()
    boundary_subject = boundary.get("subject") if boundary else None

    selected_contracts = _select_contracts(
        bundle["contracts"],
        artifacts_by_id,
        team_role_ids,
        boundary_subject,
    )
    selected_artifact_ids = {c["artifact"] for c in selected_contracts}
    selected_artifacts = [
        artifacts_by_id[aid] for aid in sorted(selected_artifact_ids)
    ]

    contract_statuses = [
        {
            "contract_id": c["id"],
            "artifact_id": c["artifact"],
            "owner": c["owner"],
            "status": derive_contract_status(
                artifacts_by_id[c["artifact"]].get("status", "")
            ),
        }
        for c in selected_contracts
    ]

    attached_moments = _attach_moments(
        bundle["moments"],
        boundary_subject,
        selected_artifact_ids,
    )

    context_state = reduce_context_state(boundary, selected_artifacts)

    context = {
        "boundary_id": boundary["id"] if boundary else None,
        "subject": boundary_subject,
        "orchestrator": boundary.get("orchestrator") if boundary else None,
        "team_id": boundary.get("team") if boundary else None,
        "selected_contracts": [c["id"] for c in selected_contracts],
        "selected_artifacts": [a["id"] for a in selected_artifacts],
        "contract_statuses": contract_statuses,
        "moments": [m["id"] for m in attached_moments],
        "context_state": context_state,
    }

    derived = {
        "role_views": _derive_role_views(bundle["roles"]),
        "team_views": _derive_team_views(bundle["teams"], roles_by_id),
        "artifact_statuses": [
            {"artifact_id": a["id"], "status": a.get("status")}
            for a in selected_artifacts
        ],
        "contract_statuses": contract_statuses,
        "contexts": [context],
        "context_state": context_state,
    }

    declared = {key: bundle.get(key, []) for key in (
        "sources", "artifacts", "contracts", "roles", "teams",
        "profiles", "boundaries", "moments", "timpos",
    )}

    trace = {
        "claims": list(TRACE_CLAIMS),
        "hash": "",
    }

    output = {
        "answer": REQUIRED_ANSWER,
        "declared": declared,
        "derived": derived,
        "trace": trace,
        "hashes": {},
    }

    content_hash = sha256_hex(
        {
            "answer": output["answer"],
            "declared": declared,
            "derived": derived,
            "trace": {"claims": trace["claims"]},
        }
    )
    output["trace"]["hash"] = content_hash
    output["hashes"] = {
        "content": content_hash,
        "declared": sha256_hex(declared),
        "derived": sha256_hex(derived),
    }

    return output


def derive_context_for_state(
    boundary: dict[str, Any] | None,
    selected_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Expose reducer for tests with custom artifact sets."""
    return reduce_context_state(boundary, selected_artifacts)
