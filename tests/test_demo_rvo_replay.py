"""Tests for the renderable RVO demo replay."""

from __future__ import annotations

import json

from demo.rvo_replay import (
    REPLAY_EVENTS,
    build_replay,
    load_rvo_fixture,
    main,
    render_replay_text,
)


def test_rvo_fixture_is_bounded_to_three_demo_agents():
    bundle = load_rvo_fixture()
    assert [agent["id"] for agent in bundle["agents"]["agents"]] == [
        "agent.director_owner",
        "agent.fde_executor",
        "agent.cva_consumer",
    ]
    assert bundle["objectives"]["objectives"] == [
        {
            "id": "objective.rvo_customer_action",
            "intent": "Coordinate RVO-style risk intelligence into customer implementation value.",
            "agents": [
                "agent.director_owner",
                "agent.fde_executor",
                "agent.cva_consumer",
            ],
            "contracts": [
                "contract.value_evidence",
                "contract.technical_evidence",
                "contract.customer_system_mapping",
                "contract.integration_path",
                "contract.roi_assumption",
            ],
        }
    ]


def test_rvo_fixture_contains_expected_artifacts():
    bundle = load_rvo_fixture()
    artifact_ids = {
        artifact["id"]
        for artifact in bundle["artifacts"]["artifacts"]
    }
    assert artifact_ids == {
        "artifact.value_evidence",
        "artifact.integration_path",
        "artifact.technical_evidence",
        "artifact.customer_system_mapping",
        "artifact.roi_assumption",
    }


def test_rvo_surface_bindings_live_in_fixture_data():
    bundle = load_rvo_fixture()
    surfaces = bundle["demo_surfaces"]
    assert surfaces["implement"]["artifacts"]["integration_path"]["id"] == (
        "artifact.integration_path"
    )
    assert surfaces["implement"]["artifacts"]["customer_mapping"]["id"] == (
        "artifact.customer_system_mapping"
    )
    assert surfaces["value"]["artifacts"]["value_narrative"]["id"] == (
        "artifact.value_evidence"
    )
    assert surfaces["value"]["claims"]["cost_impact"]["id"] == (
        "claim.unsupported_cost_impact"
    )


def test_rvo_replay_sequence_matches_minimum_slice():
    assert [event["type"] for event in REPLAY_EVENTS] == [
        "context_opened",
        "source_ref_added",
        "claim_status_set",
        "artifact_status_set",
    ]
    assert REPLAY_EVENTS[2]["claim"] == "claim.unsupported_cost_impact"
    assert REPLAY_EVENTS[2]["status"] == "rejected"
    assert REPLAY_EVENTS[3]["artifact"] == "artifact.integration_path"
    assert REPLAY_EVENTS[3]["status"] == "present"


def test_rvo_replay_renders_acceptance_before_after_text():
    before, after = build_replay()
    output = render_replay_text(before, after)
    assert "Before:" in output
    assert "  Coordinate = unresolved" in output
    assert "  Implement = blocked/missing" in output
    assert "  Value = partially supported" in output
    assert "After:" in output
    assert "  Coordinate = updated next action:" in output
    assert "  Implement = implementation path present, customer mapping missing" in output
    assert "  Value = value narrative supported, cost impact rejected" in output


def test_rvo_replay_kernel_output_is_deterministic():
    first = build_replay()[1]["kernel"]
    second = build_replay()[1]["kernel"]
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_rvo_replay_command_prints_human_readable_transcript(capsys):
    assert main([]) == 0
    output = capsys.readouterr().out
    assert output.startswith("RVO Customer Action Replay\n")
    assert "Before:" in output
    assert "After:" in output


def test_rvo_replay_command_can_emit_json(capsys):
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"before", "after"}
    assert payload["after"]["state"]["artifact_statuses"]["artifact.integration_path"] == (
        "present"
    )
