"""Validate declared object minimalism and references."""

from __future__ import annotations

from typing import Any

from corus_kernel.schemas import ALLOWED_FIELDS, COLLECTION_KEYS, MOMENT_FIELDS


class ValidationError(Exception):
    """Raised when declared objects fail validation."""


def validate_minimalism(bundle: dict[str, list[dict[str, Any]]]) -> None:
    """Fail if any declared object contains fields outside its allowed set."""
    errors: list[str] = []
    for collection, object_type in COLLECTION_KEYS.items():
        allowed = ALLOWED_FIELDS[object_type]
        for item in bundle.get(collection, []):
            extra = set(item.keys()) - allowed
            if extra:
                errors.append(
                    f"{collection} item {item.get('id', '?')}: extra fields {sorted(extra)}"
                )
    if errors:
        raise ValidationError("; ".join(errors))


def validate_moment_minimalism(moments: list[dict[str, Any]]) -> None:
    """Ensure moment atoms stay tiny."""
    errors: list[str] = []
    for moment in moments:
        extra = set(moment.keys()) - MOMENT_FIELDS
        if extra:
            errors.append(
                f"moment {moment.get('id', '?')}: extra fields {sorted(extra)}"
            )
    if errors:
        raise ValidationError("; ".join(errors))


def validate_references(bundle: dict[str, list[dict[str, Any]]]) -> None:
    """Validate that all object references resolve."""
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
        if artifact.get("subject") not in ids["source"]:
            errors.append(
                f"artifact {artifact['id']}: subject {artifact.get('subject')} not found"
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
        if profile.get("type") == "role" and ref not in ids["role"]:
            errors.append(f"profile {profile['id']}: ref {ref} not found")
        elif profile.get("type") == "system" and ref not in ids["system"]:
            errors.append(f"profile {profile['id']}: ref {ref} not found")

    for boundary in bundle.get("boundaries", []):
        if boundary.get("orchestrator") not in ids["profile"]:
            errors.append(
                f"boundary {boundary['id']}: orchestrator {boundary.get('orchestrator')} not found"
            )
        if boundary.get("team") not in ids["team"]:
            errors.append(
                f"boundary {boundary['id']}: team {boundary.get('team')} not found"
            )
        if boundary.get("subject") not in ids["source"]:
            errors.append(
                f"boundary {boundary['id']}: subject {boundary.get('subject')} not found"
            )

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


def validate_bundle(bundle: dict[str, list[dict[str, Any]]]) -> None:
    validate_minimalism(bundle)
    validate_moment_minimalism(bundle.get("moments", []))
    validate_references(bundle)
