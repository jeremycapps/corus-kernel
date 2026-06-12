"""Tests for the demo replay wrapper around the frozen v1 kernel."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from corus_v1.derive import derive
from corus_v1.load import load_project
from demo.replay import apply_event, apply_replay

REPO_ROOT = Path(__file__).resolve().parent.parent

OBJECTIVE_SPEC = "artifact.objective_spec"
AGENT_INSTRUCTIONS = "artifact.agent_execution_instructions"
OBJECT_MODEL = "artifact.object_model_spec"


@pytest.fixture
def bundle():
    return load_project(REPO_ROOT)


def test_replay_events_update_artifact_and_claim_statuses(bundle):
    result = apply_replay(
        bundle,
        [
            {
                "type": "source_ref_added",
                "source": "source.demo.rvo",
                "label": "RVO account context",
                "locator": "demo://rvo",
            },
            {
                "type": "claim_status_set",
                "claim": "claim.cost_impact",
                "status": "missing_evidence",
                "text": "Cost impact is not claimable yet.",
                "artifact": OBJECT_MODEL,
                "source_refs": ["source.demo.rvo"],
            },
            {
                "type": "artifact_status_set",
                "artifact": OBJECTIVE_SPEC,
                "status": "validated",
            },
        ],
    )

    assert result["state"]["artifact_statuses"][OBJECTIVE_SPEC] == "validated"
    assert result["state"]["claims"] == [
        {
            "artifact": OBJECT_MODEL,
            "id": "claim.cost_impact",
            "source_refs": ["source.demo.rvo"],
            "status": "missing_evidence",
            "text": "Cost impact is not claimable yet.",
        }
    ]
    assert result["state"]["source_refs"] == [
        {
            "id": "source.demo.rvo",
            "label": "RVO account context",
            "locator": "demo://rvo",
        }
    ]


def test_replay_calls_kernel_after_artifact_events(bundle):
    result = apply_replay(
        bundle,
        [
            {
                "type": "artifact_status_set",
                "artifact": OBJECTIVE_SPEC,
                "status": "validated",
            },
        ],
    )

    derived = result["kernel"]["derived"]
    assert "contract.agent_execution_instructions" in derived["unblocked_contracts"]
    assert result["surfaces"]["coordinate"]["next_executor_actions"] == [
        "contract.agent_execution_instructions"
    ]


def test_coordinate_implement_and_value_payloads_are_rendered(bundle):
    result = apply_replay(
        bundle,
        [
            {
                "type": "artifact_status_set",
                "artifact": OBJECTIVE_SPEC,
                "status": "validated",
            },
            {
                "type": "artifact_status_set",
                "artifact": AGENT_INSTRUCTIONS,
                "status": "present",
            },
            {
                "type": "claim_status_set",
                "claim": "claim.cost_impact",
                "status": "rejected",
                "text": "Do not claim cost impact yet.",
                "evidence_refs": [],
            },
            {
                "type": "claim_status_set",
                "claim": "claim.workflow_alignment",
                "status": "admitted",
                "text": "Workflow ownership is aligned.",
                "evidence_refs": ["source.demo.rvo"],
            },
        ],
    )

    surfaces = result["surfaces"]
    assert set(surfaces) == {"coordinate", "implement", "value"}
    assert surfaces["coordinate"]["surface"] == "Coordinate"
    assert surfaces["implement"]["surface"] == "Implement"
    assert surfaces["value"]["surface"] == "Value"
    assert surfaces["coordinate"]["rejected_claims"][0]["id"] == "claim.cost_impact"
    assert surfaces["implement"]["blocked_contracts"]
    assert surfaces["value"]["admitted_claims"][0]["id"] == "claim.workflow_alignment"
    assert surfaces["value"]["consumer_actions"][0]["contract"] == (
        "contract.agent_execution_instructions"
    )


def test_wrapper_consumes_reducer_output_without_altering_kernel_rules(bundle):
    before = derive(bundle)
    replayed = apply_replay(
        bundle,
        [
            {
                "type": "claim_status_set",
                "claim": "claim.demo_only",
                "status": "rejected",
                "text": "Rejected demo claim.",
            },
            {
                "type": "source_ref_added",
                "source": "source.demo",
                "label": "Demo source",
            },
        ],
    )

    assert replayed["kernel"] == before
    assert replayed["surfaces"]["coordinate"]["rejected_claims"][0]["id"] == (
        "claim.demo_only"
    )


def test_kernel_output_remains_deterministic_after_same_replay(bundle):
    events = [
        {
            "type": "artifact_status_set",
            "artifact": OBJECTIVE_SPEC,
            "status": "validated",
        },
        {
            "type": "artifact_status_set",
            "artifact": AGENT_INSTRUCTIONS,
            "status": "validated",
        },
        {
            "type": "artifact_status_set",
            "artifact": OBJECT_MODEL,
            "status": "present",
        },
    ]

    first = json.dumps(apply_replay(bundle, events)["kernel"], sort_keys=True)
    second = json.dumps(apply_replay(bundle, events)["kernel"], sort_keys=True)
    assert first == second


def test_replay_does_not_mutate_input_bundle(bundle):
    original = copy.deepcopy(bundle)
    apply_replay(
        bundle,
        [
            {
                "type": "artifact_status_set",
                "artifact": OBJECTIVE_SPEC,
                "status": "validated",
            },
        ],
    )
    assert bundle == original


def test_apply_event_rejects_unknown_event_type(bundle):
    state = {"bundle": bundle, "claims": [], "source_refs": [], "event_log": []}
    with pytest.raises(ValueError, match="Unknown replay event type"):
        apply_event(state, {"type": "unknown"})


def test_apply_event_rejects_invalid_claim_status(bundle):
    state = {"bundle": bundle, "claims": [], "source_refs": [], "event_log": []}
    with pytest.raises(ValueError, match="Invalid claim status"):
        apply_event(
            state,
            {
                "type": "claim_status_set",
                "claim": "claim.bad",
                "status": "validated",
            },
        )
