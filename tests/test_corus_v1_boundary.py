"""Boundary tests for Corus v1 coordination code."""

from __future__ import annotations

import re
from pathlib import Path

from corus_v1.derive import derive
from corus_v1.load import load_project
from corus_v1.replay_adapter import (
    object_state_map_to_artifact_status_map,
    with_artifact_status_map,
)
from timpos import Moment, Timpo, replay_to_current_state

REPO_ROOT = Path(__file__).resolve().parent.parent
CORUS_V1_DIR = REPO_ROOT / "corus_v1"


def _corus_v1_py_files() -> list[Path]:
    return sorted(CORUS_V1_DIR.glob("*.py"))


def test_corus_v1_has_no_demo_imports():
    for path in _corus_v1_py_files():
        assert "from demo" not in path.read_text(encoding="utf-8")
        assert "import demo" not in path.read_text(encoding="utf-8")


def test_corus_v1_has_no_product_terms():
    forbidden = ("Source", "Claim", "Evidence", "Surface", "Boundary", "Neara", "RAG", "UI")
    for path in _corus_v1_py_files():
        source = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert not re.search(rf"\b{re.escape(term)}\b", source), (
                f"{term} found in {path}"
            )


def test_corus_reducer_accepts_declared_artifact_statuses_without_timpos():
    result = derive(load_project(REPO_ROOT))
    assert "derived" in result
    assert result["derived"]["contracts"]
    assert result["derived"]["next_work"]["executor_actions"]


def test_replay_adapter_maps_object_state_to_artifact_status():
    object_state_map = {
        "artifact.objective_spec": "validated",
        "artifact.reducer_spec": "present",
        "opaque.other": "validated",
        "artifact.invalid": "not_a_status",
    }
    assert object_state_map_to_artifact_status_map(object_state_map) == {
        "artifact.objective_spec": "validated",
        "artifact.reducer_spec": "present",
    }


def test_corus_reducer_accepts_artifact_status_map_from_adapter():
    bundle = load_project(REPO_ROOT)
    moments = [
        Moment.create(
            timpo=Timpo.create("2026-06-13T10:00:00Z", "model:corus:self_build"),
            object="artifact.objective_spec",
            state="validated",
        ),
        Moment.create(
            timpo=Timpo.create("2026-06-13T10:01:00Z", "model:corus:self_build"),
            object="artifact.agent_execution_instructions",
            state="validated",
        ),
        Moment.create(
            timpo=Timpo.create("2026-06-13T10:02:00Z", "model:corus:self_build"),
            object="opaque.note",
            state="validated",
        ),
    ]
    artifact_status_map = object_state_map_to_artifact_status_map(
        replay_to_current_state(moments)
    )
    updated = with_artifact_status_map(bundle, artifact_status_map)
    derived = derive(updated)["derived"]
    assert "contract.object_model_spec" in derived["unblocked_contracts"]
