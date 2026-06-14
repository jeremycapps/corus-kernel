"""Tests for deterministic Fasia relation translation and packets."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from corus_v1.derive import derive, with_artifact_status
from corus_v1.load import load_project
from fasia import (
    Relation,
    Target,
    derive_implement_packet,
    derive_objective_packet,
    derive_relation_paths,
    derive_validate_packet,
    translate_relations,
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


def _target(
    target_type: str = "object",
    target_id: str = "artifact.integration_path",
) -> Target:
    return Target(type=target_type, id=target_id, label="Integration path")


def _relation(
    target_type: str = "object",
    target_id: str = "artifact.integration_path",
) -> Relation:
    return Relation(
        id="relation.rvo_output.integration_path",
        initiator="artifact.rvo_output",
        target=_target(target_type, target_id),
        sources=("source.neara_rvo_context",),
        objectives=("objective.customer_system_mapping",),
    )


def test_relation_requires_declared_edge_fields():
    relation = Relation(
        id="relation.rvo_output.integration_path",
        initiator="artifact.rvo_output",
        target=Target(
            type="object",
            id="artifact.integration_path",
            label="Integration path",
        ),
        sources=("source.neara_rvo_context",),
        objectives=("objective.customer_system_mapping",),
    )

    assert relation.as_dict() == {
        "id": "relation.rvo_output.integration_path",
        "initiator": "artifact.rvo_output",
        "target": {
            "type": "object",
            "id": "artifact.integration_path",
            "label": "Integration path",
        },
        "sources": ["source.neara_rvo_context"],
        "objectives": ["objective.customer_system_mapping"],
    }


def test_relation_rejects_empty_fields():
    with pytest.raises(ValueError, match="Relation.initiator"):
        Relation(
            id="relation.rvo_output.integration_path",
            initiator="",
            target=_target(),
            sources=("source.neara_rvo_context",),
            objectives=("objective.customer_system_mapping",),
        )


def test_relation_requires_sources_and_objectives():
    with pytest.raises(ValueError, match="Relation.sources"):
        Relation(
            id="relation.rvo_output.integration_path",
            initiator="artifact.rvo_output",
            target=_target(),
            sources=(),
            objectives=("objective.customer_system_mapping",),
        )
    with pytest.raises(ValueError, match="Relation.objectives"):
        Relation(
            id="relation.rvo_output.integration_path",
            initiator="artifact.rvo_output",
            target=_target(),
            sources=("source.neara_rvo_context",),
            objectives=(),
        )


def test_relation_rejects_non_v0_reference_prefixes():
    with pytest.raises(ValueError, match="Relation.sources entries"):
        Relation(
            id="relation.rvo_output.integration_path",
            initiator="artifact.rvo_output",
            target=_target(),
            sources=("document.neara_rvo_context",),
            objectives=("objective.customer_system_mapping",),
        )
    with pytest.raises(ValueError, match="Relation.objectives entries"):
        Relation(
            id="relation.rvo_output.integration_path",
            initiator="artifact.rvo_output",
            target=_target(),
            sources=("source.neara_rvo_context",),
            objectives=("workflow.customer_system_mapping",),
        )


def test_target_type_must_be_object_or_subject():
    with pytest.raises(ValueError, match="Target.type"):
        Target(type="workflow", id="artifact.integration_path", label="Integration path")


def test_relation_does_not_accept_removed_fields():
    removed_fields = (
        "state",
        "depends_on",
        "requires",
        "predicate",
        "mode",
        "target_role",
        "context",
        "context_view",
    )
    base = {
        "id": "relation.rvo_output.integration_path",
        "initiator": "artifact.rvo_output",
        "target": _target(),
        "sources": ("source.neara_rvo_context",),
        "objectives": ("objective.customer_system_mapping",),
    }
    for field in removed_fields:
        with pytest.raises(TypeError):
            Relation(**{**base, field: "not_allowed"})


def test_fasia_derives_object_and_subject_labels_from_path():
    object_relation = _relation(target_type="object")
    subject_relation = Relation(
        id="relation.rvo_output.customer_team",
        initiator="artifact.rvo_output",
        target=Target(type="subject", id="subject.customer_team", label="Customer team"),
        sources=("source.neara_rvo_context",),
        objectives=("objective.customer_system_mapping",),
    )

    open_paths = derive_relation_paths(
        [object_relation, subject_relation],
        admitted_sources=("source.neara_rvo_context",),
        active_objectives=("objective.customer_system_mapping",),
        node_states={
            "artifact.rvo_output": "present",
            "artifact.integration_path": "present",
            "subject.customer_team": "present",
        },
    )
    closed_paths = derive_relation_paths(
        [object_relation, subject_relation],
        admitted_sources=(),
        active_objectives=("objective.customer_system_mapping",),
        node_states={
            "artifact.rvo_output": "present",
            "artifact.integration_path": "present",
            "subject.customer_team": "present",
        },
    )

    open_by_relation = {item["relation"]: item for item in open_paths}
    closed_by_relation = {item["relation"]: item for item in closed_paths}

    assert (open_by_relation[object_relation.id]["path"], open_by_relation[object_relation.id]["label"]) == (
        "open",
        "enables",
    )
    assert (open_by_relation[subject_relation.id]["path"], open_by_relation[subject_relation.id]["label"]) == (
        "open",
        "affects",
    )
    assert (
        closed_by_relation[object_relation.id]["path"],
        closed_by_relation[object_relation.id]["label"],
    ) == ("closed", "blocks")
    assert (
        closed_by_relation[subject_relation.id]["path"],
        closed_by_relation[subject_relation.id]["label"],
    ) == ("closed", "risks")


def test_fasia_derives_closed_path_when_corus_blocks_target_artifact():
    path = derive_relation_paths(
        [_relation()],
        admitted_sources=("source.neara_rvo_context",),
        active_objectives=("objective.customer_system_mapping",),
        node_states={
            "artifact.rvo_output": "present",
            "artifact.integration_path": "present",
        },
        corus_blocked_artifacts=("artifact.integration_path",),
    )[0]

    assert path == {
        "relation": "relation.rvo_output.integration_path",
        "path": "closed",
        "label": "blocks",
        "reasons": ["target_blocked_by_corus_readiness"],
    }


def test_fasia_derives_closed_path_when_source_is_not_admitted():
    path = derive_relation_paths(
        [_relation()],
        admitted_sources=(),
        active_objectives=("objective.customer_system_mapping",),
        node_states={
            "artifact.rvo_output": "present",
            "artifact.integration_path": "present",
        },
    )[0]

    assert path["path"] == "closed"
    assert path["label"] == "blocks"
    assert path["reasons"] == ["source_not_admitted"]


def test_fasia_derives_closed_path_when_objective_is_outside_scope():
    path = derive_relation_paths(
        [_relation()],
        admitted_sources=("source.neara_rvo_context",),
        active_objectives=("objective.other",),
        node_states={
            "artifact.rvo_output": "present",
            "artifact.integration_path": "present",
        },
    )[0]

    assert path["path"] == "closed"
    assert path["label"] == "blocks"
    assert path["reasons"] == ["objective_out_of_scope"]


def test_translation_edges_are_deterministic_relation_edges():
    relations = [_relation()]

    discovery = translate_relations(
        relations,
        "discovery",
        admitted_sources=("source.neara_rvo_context",),
        active_objectives=("objective.customer_system_mapping",),
        node_states={
            "artifact.rvo_output": "present",
            "artifact.integration_path": "present",
        },
        input_refs=("artifact.rvo_output",),
        output_refs=("artifact.integration_path",),
    )
    strategy = translate_relations(
        relations,
        "strategy",
        admitted_sources=("source.neara_rvo_context",),
        active_objectives=("objective.customer_system_mapping",),
    )
    product = translate_relations(
        relations,
        "product",
        admitted_sources=("source.neara_rvo_context",),
        active_objectives=("objective.customer_system_mapping",),
    )

    assert discovery["translation"] == {
        "mode": "discovery",
        "source": "consumer",
        "target": "objective",
        "input_refs": ["artifact.rvo_output"],
        "output_refs": ["artifact.integration_path"],
    }
    assert discovery["derived_relations"][0]["path"] == "open"
    assert discovery["derived_relations"][0]["label"] == "enables"
    assert strategy["translation"]["source"] == "objective"
    assert strategy["translation"]["target"] == "value"
    assert product["translation"]["source"] == "value"
    assert product["translation"]["target"] == "consumer"


def test_unknown_translation_mode_is_rejected():
    with pytest.raises(ValueError, match="Unknown translation mode"):
        translate_relations(
            [],
            "handoff",
            admitted_sources=(),
            active_objectives=(),
        )


def test_objective_packet_projects_objective_scope():
    bundle = _bundle_with_statuses({
        OBJECTIVE_SPEC: "validated",
        AGENT_INSTRUCTIONS: "present",
    })
    flow, objective, contracts, artifacts = _inputs(bundle)
    packet = derive_objective_packet(flow, objective, contracts, artifacts)

    assert packet["packet"] == {
        "id": "packet.objective",
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


def test_implement_packet_filters_by_executor():
    bundle = _bundle_with_statuses({
        OBJECTIVE_SPEC: "validated",
        AGENT_INSTRUCTIONS: "validated",
    })
    flow, _objective, contracts, artifacts = _inputs(bundle)
    packet = derive_implement_packet(
        flow,
        "agent.systems_architect",
        contracts,
        artifacts,
    )

    assert packet["packet"]["relation"] == "executor"
    assert packet["packet"]["actor"] == "agent.systems_architect"
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


def test_validate_packet_filters_by_consumer():
    bundle = _bundle_with_statuses({
        OBJECTIVE_SPEC: "validated",
        AGENT_INSTRUCTIONS: "validated",
        OBJECT_MODEL: "present",
        REDUCER_SPEC: "rejected",
    })
    flow, _objective, contracts, artifacts = _inputs(bundle)
    packet = derive_validate_packet(
        flow,
        "agent.systems_engineer",
        contracts,
        artifacts,
    )

    assert packet["packet"]["relation"] == "consumer"
    assert packet["packet"]["actor"] == "agent.systems_engineer"
    assert packet["queues"]["needs_validation"] == []
    assert packet["queues"]["rejected"] == ["artifact.reducer_spec"]
    assert packet["contracts"]["needs_validation"] == []
    assert packet["contracts"]["rejected"] == ["contract.reducer_spec"]
    assert packet["actions"]["available"] == []

    ui_packet = derive_validate_packet(
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


def test_packet_projection_is_deterministic():
    bundle = _bundle_with_statuses({OBJECTIVE_SPEC: "validated"})
    flow, objective, contracts, artifacts = _inputs(bundle)
    first = derive_objective_packet(flow, objective, contracts, artifacts)
    second = derive_objective_packet(flow, objective, contracts, artifacts)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_packet_projection_does_not_mutate_flow():
    bundle = _bundle_with_statuses({OBJECTIVE_SPEC: "validated"})
    flow, objective, contracts, artifacts = _inputs(bundle)
    before = copy.deepcopy(flow)
    derive_objective_packet(flow, objective, contracts, artifacts)
    derive_implement_packet(flow, "agent.product_strategy", contracts, artifacts)
    derive_validate_packet(flow, "agent.systems_architect", contracts, artifacts)
    assert flow == before


def test_corus_v1_does_not_import_fasia():
    for path in CORUS_V1_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "from fasia" not in source
        assert "import fasia" not in source


def test_fasia_does_not_import_demo_or_rendering_code():
    forbidden = ("from demo", "import demo", "React", "HTML", "CSS", "dashboard")
    for path in FASIA_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in source, f"{term} found in {path}"


def test_fasia_does_not_define_timpos_or_corus_primitives():
    forbidden = (
        "class Moment",
        "class Contract",
        "class Artifact",
        "Artifact.requires",
        "\"requires\"",
        "'requires'",
    )
    for path in FASIA_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in source, f"{term} found in {path}"


def test_fasia_consumes_readiness_only_through_explicit_inputs():
    for path in FASIA_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "from corus_v1" not in source
        assert "import corus_v1" not in source
        assert "from timpos" not in source
        assert "import timpos" not in source


def test_fasia_does_not_define_owner_role():
    for path in FASIA_DIR.glob("*.py"):
        assert "owner" not in path.read_text(encoding="utf-8").lower()


def test_fasia_does_not_encode_product_or_role_labels():
    forbidden = (
        "Coordinate",
        "Implement",
        "Neara",
        "Director",
        "FDE",
        "CVA",
        "Engineer",
        "Architect",
        "Owner",
        "LLM",
    )
    for path in FASIA_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in source, f"{term} found in {path}"
