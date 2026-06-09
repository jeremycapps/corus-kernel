"""Validate declared objects: schema, references, and runtime warnings."""

from __future__ import annotations

from typing import Any

from corus_kernel.schemas import (
    ALLOWED_FIELDS,
    ARTIFACT_STATUSES,
    COLLECTION_KEYS,
    MOMENT_FIELDS,
    PROFILE_TYPES,
    REQUIRED_FIELDS,
    SOURCE_TYPES,
)


class ValidationError(Exception):
    """Raised when declared objects fail strict validation."""


def _validate_item_fields(
    collection: str,
    object_type: str,
    item: dict[str, Any],
    errors: list[str],
) -> None:
    allowed = ALLOWED_FIELDS[object_type]
    required = REQUIRED_FIELDS[object_type]
    item_id = item.get("id", "?")

    extra = set(item.keys()) - allowed
    if extra:
        errors.append(
            f"{collection} item {item_id}: extra fields {sorted(extra)}"
        )

    missing = required - set(item.keys())
    if missing:
        errors.append(
            f"{collection} item {item_id}: missing fields {sorted(missing)}"
        )


def _validate_enums(bundle: dict[str, list[dict[str, Any]]], errors: list[str]) -> None:
    for source in bundle.get("sources", []):
        source_type = source.get("type")
        if source_type is not None and source_type not in SOURCE_TYPES:
            errors.append(
                f"sources item {source.get('id', '?')}: invalid type {source_type!r}"
            )

    for artifact in bundle.get("artifacts", []):
        status = artifact.get("status")
        if status is not None and status not in ARTIFACT_STATUSES:
            errors.append(
                f"artifacts item {artifact.get('id', '?')}: "
                f"invalid status {status!r}"
            )

    for profile in bundle.get("profiles", []):
        profile_type = profile.get("type")
        if profile_type is not None and profile_type not in PROFILE_TYPES:
            errors.append(
                f"profiles item {profile.get('id', '?')}: "
                f"invalid type {profile_type!r}"
            )


def validate_schema(bundle: dict[str, list[dict[str, Any]]]) -> None:
    """Strict schema validation: required fields, allowed fields, and enums."""
    errors: list[str] = []

    for collection, object_type in COLLECTION_KEYS.items():
        for item in bundle.get(collection, []):
            _validate_item_fields(collection, object_type, item, errors)

    _validate_enums(bundle, errors)

    if errors:
        raise ValidationError("; ".join(errors))


def validate_minimalism(bundle: dict[str, list[dict[str, Any]]]) -> None:
    """Alias for validate_schema."""
    validate_schema(bundle)


def validate_unique_ids(bundle: dict[str, list[dict[str, Any]]]) -> None:
    """Fail on duplicate ids within a collection or across declared objects."""
    errors: list[str] = []
    seen_global: dict[str, str] = {}

    for collection in COLLECTION_KEYS:
        seen_local: set[str] = set()
        for item in bundle.get(collection, []):
            item_id = item.get("id")
            if not item_id:
                continue
            if item_id in seen_local:
                errors.append(
                    f"{collection}: duplicate id {item_id} within collection"
                )
            seen_local.add(item_id)

            if item_id in seen_global:
                errors.append(
                    f"duplicate id {item_id} in {collection} "
                    f"(already declared in {seen_global[item_id]})"
                )
            else:
                seen_global[item_id] = collection

    if errors:
        raise ValidationError("; ".join(errors))


def validate_references(bundle: dict[str, list[dict[str, Any]]]) -> None:
    """Strict reference validation for declared object links."""
    ids: dict[str, set[str]] = {
        "source": {s["id"] for s in bundle.get("sources", [])},
        "artifact": {a["id"] for a in bundle.get("artifacts", [])},
        "contract": {c["id"] for c in bundle.get("contracts", [])},
        "role": {r["id"] for r in bundle.get("roles", [])},
        "team": {t["id"] for t in bundle.get("teams", [])},
        "profile": {p["id"] for p in bundle.get("profiles", [])},
        "boundary": {b["id"] for b in bundle.get("boundaries", [])},
        "moment": {m["id"] for m in bundle.get("moments", [])},
        "timpo": {t["id"] for t in bundle.get("timpos", [])},
    }
    ids["system"] = {"system.corus"}

    errors: list[str] = []

    for artifact in bundle.get("artifacts", []):
        subject = artifact.get("subject")
        if subject and subject not in ids["source"]:
            errors.append(
                f"artifact {artifact['id']}: subject {subject} not found"
            )
        for origin in artifact.get("origin", []):
            if origin not in ids["source"]:
                errors.append(
                    f"artifact {artifact['id']}: origin {origin} not found"
                )

    for contract in bundle.get("contracts", []):
        if contract.get("owner") not in ids["role"]:
            errors.append(
                f"contract {contract['id']}: owner {contract.get('owner')} not found"
            )
        if contract.get("artifact") not in ids["artifact"]:
            errors.append(
                f"contract {contract['id']}: artifact {contract.get('artifact')} not found"
            )

    for team in bundle.get("teams", []):
        for role_id in team.get("roles", []):
            if role_id not in ids["role"]:
                errors.append(f"team {team['id']}: role {role_id} not found")

    for profile in bundle.get("profiles", []):
        ref = profile.get("ref")
        profile_type = profile.get("type")
        if profile_type == "role" and ref not in ids["role"]:
            errors.append(f"profile {profile['id']}: ref {ref} not found")
        elif profile_type == "team" and ref not in ids["team"]:
            errors.append(f"profile {profile['id']}: ref {ref} not found")
        elif profile_type == "system" and ref not in ids["system"]:
            errors.append(f"profile {profile['id']}: ref {ref} not found")

    for moment in bundle.get("moments", []):
        if moment.get("timpo") not in ids["timpo"]:
            errors.append(
                f"moment {moment['id']}: timpo {moment.get('timpo')} not found"
            )
        if moment.get("actor") not in ids["profile"]:
            errors.append(
                f"moment {moment['id']}: actor {moment.get('actor')} not found"
            )
        prev = moment.get("previous")
        if prev is not None and prev not in ids["moment"]:
            errors.append(f"moment {moment['id']}: previous {prev} not found")

    if errors:
        raise ValidationError("; ".join(errors))


def collect_resolution_warnings(
    bundle: dict[str, list[dict[str, Any]]],
    boundary: dict[str, Any] | None,
) -> list[str]:
    """Non-fatal runtime warnings during boundary resolution."""
    warnings: list[str] = []
    sources_by_id = {s["id"]: s for s in bundle.get("sources", [])}
    teams_by_id = {t["id"]: t for t in bundle.get("teams", [])}
    profiles_by_id = {p["id"]: p for p in bundle.get("profiles", [])}

    if boundary is None:
        warnings.append("No boundary selected for resolution.")
        return warnings

    boundary_id = boundary.get("id", "?")
    subject = boundary.get("subject")
    if not subject:
        warnings.append(f"Boundary {boundary_id}: subject missing; context blocked.")
    elif subject not in sources_by_id:
        warnings.append(
            f"Boundary {boundary_id}: subject {subject} not found; context blocked."
        )

    team_id = boundary.get("team")
    if not team_id:
        warnings.append(f"Boundary {boundary_id}: team missing; context blocked.")
    elif team_id not in teams_by_id:
        warnings.append(f"Boundary {boundary_id}: team {team_id} not found.")

    orchestrator = boundary.get("orchestrator")
    if not orchestrator:
        warnings.append(
            f"Boundary {boundary_id}: orchestrator missing; context blocked."
        )
    elif orchestrator not in profiles_by_id:
        warnings.append(
            f"Boundary {boundary_id}: orchestrator {orchestrator} not found."
        )

    return warnings


def validate_bundle(bundle: dict[str, list[dict[str, Any]]]) -> None:
    validate_schema(bundle)
    validate_unique_ids(bundle)
    validate_references(bundle)
