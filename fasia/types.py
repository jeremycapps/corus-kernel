"""Shared helpers for surface packet projections."""

from __future__ import annotations

from typing import Any


def index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def contract_states_by_id(flow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(flow.get("contracts", []))


def objective_states_by_id(flow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(flow.get("objectives", []))


def artifact_statuses(artifacts: list[dict[str, Any]]) -> dict[str, str]:
    return {
        artifact["id"]: artifact["status"]
        for artifact in sorted(artifacts, key=lambda item: item["id"])
    }


def produced_artifacts(contract_state: dict[str, Any]) -> list[str]:
    return list(contract_state.get("produces", []))


def submit_action_id(artifact_id: str) -> str:
    return f"action.submit.{artifact_id}"


def validate_action_id(artifact_id: str) -> str:
    return f"action.validate.{artifact_id}"


def reject_action_id(artifact_id: str) -> str:
    return f"action.reject.{artifact_id}"
