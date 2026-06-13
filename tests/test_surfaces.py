"""Tests for deterministic relation-scoped surface packets."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from corus_v1.derive import derive, with_artifact_status
from corus_v1.load import load_project
from fasia import (
    derive_implement_surface,
    derive_objective_surface,
    derive_validate_surface,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FASIA_DIR = REPO_ROOT / "fasia"
CORUS_V1_DIR = REPO_ROOT / "corus_v1"

OBJECTIVE_SPEC = "artifact.objective_spec"
AGENT_INSTRUCTIONS = "artifact.agent_execution_instructions"
OBJECT_MODEL = "artifact.object_model_spec"
REDUCER_SPEC = "artifact.reducer_spec"


def _bundle_with_statuses(statuses: dict[str, str]) -> dict:
    bundle = load_project(REPO_ROOT)
    for artifact_id, status in statuses.items():
        bundle = with_artifact_status(bundle, artifact_id, status)
    return bundle


def _inputs(bundle: dict) -> tuple[dict, dict, list[dict], list[dict]]:
    flow = derive(bundle)["derived"]
    objective = bundle["objectives"]["objectives"][0]
    contracts = bundle["contracts"]["contracts"]
    artifacts = bundle["artifacts"]["artifacts"]
    return flow, objective, contracts, artifacts


def test_objective_surface_projects_objective_scope():
    bundle = _bundle_with_statuses({
        OBJECTIVE_SPEC: "validated",
        AGENT_INSTRUCTIONS: "present",
    })
    flow, objective, contracts, artifacts = _inputs(bundle)
    packet = derive_objective_surface(flow, objective, contracts, artifacts)

    assert packet["surface"] == {
        "id": "surface.objective",
        "type": "objective",
        "relation": "objective_scope",
        "subject": "objective.corus_self_build_engine",
    }
    assert packet["summary"]["objective_state"] == "unsatisfied"
    assert "contract.agent_execution_instructions" in packet["queues"]["needs_validation"]
    assert "artifact.agent_execution_instructions" in packet["next"]["required_validation"]
    assert packet["trace"]["derived_from"] == [
        "objective.corus_self_build_engine",
        "contracts",
        "artifacts",
        "flow",
    ]


def test_implement_surface_filters_by_executor():
    bundle = _bundle_with_statuses({
        OBJECTIVE_SPEC: "validated",
        AGENT_INSTRUCTIONS: "validated",
    })
    flow, _objective, contracts, artifacts = _inputs(bundle)
    packet = derive_implement_surface(
        flow,
        "agent.systems_architect",
        contracts,
        artifacts,
    )

    assert packet["surface"]["relation"] == "executor"
    assert packet["surface"]["actor"] == "agent.systems_architect"
    assert packet["queues"]["ready_to_execute"] == ["contract.object_model_spec"]
    assert "contract.reducer_spec" in packet["queues"]["blocked"]
    assert packet["producible"] == {
        "contract.object_model_spec": ["artifact.object_model_spec"]
    }
    assert packet["actions"]["available"] == [
        "action.submit.artifact.object_model_spec"
    ]
    assert all(
        contract_id.startswith("contract.object_model")
        or contract_id.startswith("contract.reducer")
        for contract_id in packet["trace"]["derived_from"]
    )


def test_validate_surface_filters_by_consumer():
    bundle = _bundle_with_statuses({
        OBJECTIVE_SPEC: "validated",
        AGENT_INSTRUCTIONS: "validated",
        OBJECT_MODEL: "present",
        REDUCER_SPEC: "rejected",
    })
    flow, _objective, contracts, artifacts = _inputs(bundle)
    packet = derive_validate_surface(
        flow,
        "agent.systems_engineer",
        contracts,
        artifacts,
    )

    assert packet["surface"]["relation"] == "consumer"
    assert packet["surface"]["actor"] == "agent.systems_engineer"
    assert packet["queues"]["needs_validation"] == []
    assert packet["queues"]["rejected"] == ["artifact.reducer_spec"]
    assert packet["contracts"]["needs_validation"] == []
    assert packet["contracts"]["rejected"] == ["contract.reducer_spec"]
    assert packet["actions"]["available"] == []

    ui_packet = derive_validate_surface(
        flow,
        "agent.ui_ux",
        contracts,
        artifacts,
    )
    assert ui_packet["queues"]["needs_validation"] == ["artifact.object_model_spec"]
    assert ui_packet["contracts"]["needs_validation"] == ["contract.object_model_spec"]
    assert ui_packet["actions"]["available"] == [
        "action.validate.artifact.object_model_spec",
        "action.reject.artifact.object_model_spec",
    ]


def test_surface_projection_is_deterministic():
    bundle = _bundle_with_statuses({OBJECTIVE_SPEC: "validated"})
    flow, objective, contracts, artifacts = _inputs(bundle)
    first = derive_objective_surface(flow, objective, contracts, artifacts)
    second = derive_objective_surface(flow, objective, contracts, artifacts)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_surface_projection_does_not_mutate_flow():
    bundle = _bundle_with_statuses({OBJECTIVE_SPEC: "validated"})
    flow, objective, contracts, artifacts = _inputs(bundle)
    before = copy.deepcopy(flow)
    derive_objective_surface(flow, objective, contracts, artifacts)
    derive_implement_surface(flow, "agent.product_strategy", contracts, artifacts)
    derive_validate_surface(flow, "agent.systems_architect", contracts, artifacts)
    assert flow == before


def test_corus_v1_does_not_import_surfaces():
    for path in CORUS_V1_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "from fasia" not in source
        assert "import fasia" not in source


def test_surfaces_do_not_import_demo_or_ui():
    forbidden = ("from demo", "import demo", "React", "HTML", "CSS", "dashboard")
    for path in FASIA_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in source, f"{term} found in {path}"


def test_surfaces_do_not_define_owner_role():
    for path in FASIA_DIR.glob("*.py"):
        assert "owner" not in path.read_text(encoding="utf-8").lower()


def test_surfaces_do_not_encode_job_titles():
    forbidden = ("Director", "FDE", "CVA", "Engineer", "Architect", "Strategy")
    for path in FASIA_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in source, f"{term} found in {path}"
