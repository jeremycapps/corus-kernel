"""Derive context from declared objects."""

from __future__ import annotations

from typing import Any

from corus_kernel.hash import sha256_hex
from corus_kernel.loader import index_by_id, load_bundle
from corus_kernel.validate import (
    collect_resolution_warnings,
    validate_references,
    validate_schema,
    validate_unique_ids,
)

ARTIFACT_STATUSES_BLOCKING = {"expected_missing", "rejected"}
ARTIFACT_STATUSES_READY = {"present", "validated"}


class BoundarySelectionError(Exception):
    """Raised when boundary selection is ambiguous or invalid."""


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
    *,
    subject_resolved: bool = True,
    team_resolved: bool = True,
) -> dict[str, Any]:
    """Default context state reducer."""
    if boundary is None or not boundary.get("subject") or not subject_resolved:
        return {
            "coordination": "blocked",
            "reason": "missing_subject",
        }

    if not boundary.get("team") or not team_resolved:
        return {
            "coordination": "blocked",
            "reason": "missing_team",
        }

    if not selected_artifacts:
        return {
            "coordination": "unresolved",
            "reason": "no_selected_artifacts",
        }

    statuses = [a.get("status") for a in selected_artifacts]
    if any(s in ARTIFACT_STATUSES_BLOCKING for s in statuses):
        return {
            "coordination": "unresolved",
            "reason": "missing_or_rejected_artifacts",
        }
    if all(s in ARTIFACT_STATUSES_READY for s in statuses):
        return {
            "coordination": "ready",
            "reason": "selected_artifacts_satisfied",
        }
    return {
        "coordination": "unresolved",
        "reason": "missing_or_rejected_artifacts",
    }


def resolve_boundary(
    boundaries: list[dict[str, Any]],
    boundary_id: str | None = None,
) -> dict[str, Any] | None:
    """Select boundary by id, or auto-select when exactly one exists."""
    if not boundaries:
        return None
    if boundary_id:
        for boundary in boundaries:
            if boundary["id"] == boundary_id:
                return boundary
        raise BoundarySelectionError(f"Boundary not found: {boundary_id}")
    if len(boundaries) == 1:
        return boundaries[0]
    ids = ", ".join(b["id"] for b in boundaries)
    raise BoundarySelectionError(
        f"Multiple boundaries declared ({ids}). "
        "Specify one with --boundary <id>."
    )


def _label(objects_by_id: dict[str, dict[str, Any]], obj_id: str | None) -> str:
    if not obj_id:
        return ""
    return objects_by_id.get(obj_id, {}).get("label", obj_id)


def _profile_label(
    profiles_by_id: dict[str, dict[str, Any]],
    roles_by_id: dict[str, dict[str, Any]],
    profile_id: str | None,
) -> str:
    if not profile_id:
        return ""
    profile = profiles_by_id.get(profile_id, {})
    if profile.get("type") == "role":
        return _label(roles_by_id, profile.get("ref"))
    return profile_id


def _select_contracts(
    contracts: list[dict[str, Any]],
    artifacts_by_id: dict[str, dict[str, Any]],
    team_role_ids: set[str],
    boundary_subject: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for contract in contracts:
        owner = contract.get("owner")
        artifact = artifacts_by_id.get(contract.get("artifact", ""))
        if owner not in team_role_ids:
            excluded.append(
                {
                    "contract_id": contract["id"],
                    "reason": "owner_not_on_team",
                }
            )
            continue
        if artifact is None:
            excluded.append(
                {
                    "contract_id": contract["id"],
                    "reason": "artifact_not_found",
                }
            )
            continue
        if artifact.get("subject") != boundary_subject:
            excluded.append(
                {
                    "contract_id": contract["id"],
                    "reason": "artifact_subject_mismatch",
                }
            )
            continue
        selected.append(contract)
    return selected, excluded


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


def generate_trace_claims(
    boundary: dict[str, Any] | None,
    team_role_ids: set[str],
    selected_contracts: list[dict[str, Any]],
    excluded_contracts: list[dict[str, Any]],
    selected_artifacts: list[dict[str, Any]],
    context_state: dict[str, Any],
    roles_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    """Build trace claims from reducer events."""
    claims: list[str] = []

    if boundary is None:
        claims.append("No boundary selected.")
        claims.append(
            f"Context state resolved: {context_state['coordination']} "
            f"({context_state['reason']})."
        )
        return claims

    claims.append(
        f"Boundary {boundary['id']} ({boundary.get('label', boundary['id'])}) selected."
    )

    if boundary.get("orchestrator"):
        claims.append(
            f"Orchestrator {boundary['orchestrator']} assigned to boundary."
        )

    if boundary.get("team"):
        role_labels = [
            roles_by_id[rid]["label"]
            for rid in sorted(team_role_ids)
            if rid in roles_by_id
        ]
        claims.append(
            f"Eligible team roles: {', '.join(role_labels) if role_labels else 'none'}."
        )

    for contract in selected_contracts:
        claims.append(
            f"Contract {contract['id']} selected: owner on team and "
            "artifact.subject matches boundary subject."
        )

    for item in excluded_contracts:
        claims.append(
            f"Contract {item['contract_id']} excluded: {item['reason']}."
        )

    for artifact in selected_artifacts:
        claims.append(
            f"Artifact {artifact['id']} status read: {artifact.get('status')}."
        )

    claims.append(
        f"Context state resolved: {context_state['coordination']} "
        f"({context_state['reason']})."
    )
    return claims


def generate_answer(
    boundary: dict[str, Any] | None,
    subject_label: str,
    orchestrator_label: str,
    team_label: str,
    selected_contracts: list[dict[str, Any]],
    selected_artifacts: list[dict[str, Any]],
    context_state: dict[str, Any],
) -> str:
    """Generate human-readable answer from derived context data."""
    if boundary is None:
        return (
            "No boundary selected. "
            f"Derived context coordination is {context_state['coordination']} "
            f"({context_state['reason']})."
        )

    boundary_label = boundary.get("label", boundary.get("id", ""))
    parts = [
        f"{subject_label or boundary.get('subject', 'unknown')} is the subject "
        f"of the {boundary_label} boundary."
    ]

    if orchestrator_label:
        parts.append(f"{orchestrator_label} orchestrates the boundary.")
    if team_label:
        parts.append(f"{team_label} supplies the eligible team roles.")

    if selected_contracts:
        contract_labels = ", ".join(c["id"] for c in selected_contracts)
        parts.append(f"Selected contracts: {contract_labels}.")

    if selected_artifacts:
        artifact_parts = [
            f"{a.get('label', a['id'])} ({a.get('status')})"
            for a in selected_artifacts
        ]
        parts.append(f"Selected artifacts: {', '.join(artifact_parts)}.")

    parts.append(
        f"Derived context coordination is {context_state['coordination']} "
        f"({context_state['reason']})."
    )
    return " ".join(parts)


def derive_context(
    fixture_dir: str | Any,
    boundary_id: str | None = None,
) -> dict[str, Any]:
    """Load declared objects, validate, derive context, and emit deterministic JSON."""
    bundle = load_bundle(fixture_dir)
    validate_schema(bundle)
    validate_unique_ids(bundle)
    validate_references(bundle)

    roles_by_id = index_by_id(bundle["roles"])
    artifacts_by_id = index_by_id(bundle["artifacts"])
    teams_by_id = index_by_id(bundle["teams"])
    sources_by_id = index_by_id(bundle["sources"])
    profiles_by_id = index_by_id(bundle["profiles"])

    boundary = resolve_boundary(bundle.get("boundaries", []), boundary_id)
    warnings = collect_resolution_warnings(bundle, boundary)

    boundary_subject = boundary.get("subject") if boundary else None
    boundary_team_id = boundary.get("team") if boundary else None
    subject_resolved = bool(
        boundary_subject and boundary_subject in sources_by_id
    )
    team_resolved = bool(boundary_team_id and boundary_team_id in teams_by_id)

    team = teams_by_id.get(boundary_team_id) if team_resolved else None
    team_role_ids = set(team.get("roles", [])) if team else set()

    selected_contracts, excluded_contracts = _select_contracts(
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

    context_state = reduce_context_state(
        boundary,
        selected_artifacts,
        subject_resolved=subject_resolved,
        team_resolved=team_resolved,
    )

    subject_label = _label(sources_by_id, boundary_subject)
    orchestrator_label = _profile_label(
        profiles_by_id,
        roles_by_id,
        boundary.get("orchestrator") if boundary else None,
    )
    team_label = _label(teams_by_id, boundary.get("team") if boundary else None)

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

    declared = {
        key: bundle.get(key, [])
        for key in (
            "sources",
            "artifacts",
            "contracts",
            "roles",
            "teams",
            "profiles",
            "boundaries",
            "moments",
            "timpos",
        )
    }

    trace_claims = generate_trace_claims(
        boundary,
        team_role_ids,
        selected_contracts,
        excluded_contracts,
        selected_artifacts,
        context_state,
        roles_by_id,
    )

    answer = generate_answer(
        boundary,
        subject_label,
        orchestrator_label,
        team_label,
        selected_contracts,
        selected_artifacts,
        context_state,
    )

    trace = {"claims": trace_claims, "hash": ""}
    output = {
        "answer": answer,
        "declared": declared,
        "derived": derived,
        "trace": trace,
        "warnings": warnings,
        "hashes": {},
    }

    content_hash = sha256_hex(
        {
            "answer": output["answer"],
            "declared": declared,
            "derived": derived,
            "trace": {"claims": trace["claims"]},
            "warnings": warnings,
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
    *,
    subject_resolved: bool = True,
    team_resolved: bool = True,
) -> dict[str, Any]:
    """Expose reducer for tests with custom artifact sets."""
    return reduce_context_state(
        boundary,
        selected_artifacts,
        subject_resolved=subject_resolved,
        team_resolved=team_resolved,
    )
