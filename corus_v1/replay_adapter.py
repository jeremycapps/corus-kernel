"""Adapter from replayed object state into Corus artifact status."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

ARTIFACT_STATUS_VALUES = {
    "expected_missing",
    "present",
    "validated",
    "rejected",
}


def object_state_map_to_artifact_status_map(
    object_state_map: Mapping[str, str],
) -> dict[str, str]:
    artifact_status_map: dict[str, str] = {}
    for object_id, state in object_state_map.items():
        if not object_id.startswith("artifact."):
            continue
        if state not in ARTIFACT_STATUS_VALUES:
            continue
        artifact_status_map[object_id] = state
    return artifact_status_map


def with_artifact_status_map(
    bundle: dict[str, Any],
    artifact_status_map: Mapping[str, str],
) -> dict[str, Any]:
    updated = copy.deepcopy(bundle)
    for artifact in updated.get("artifacts", {}).get("artifacts", []):
        artifact_id = artifact["id"]
        if artifact_id in artifact_status_map:
            artifact["status"] = artifact_status_map[artifact_id]
    return updated
