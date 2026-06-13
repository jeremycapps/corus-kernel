"""Tests for the renderable RVO step replay."""

from __future__ import annotations

import json
from pathlib import Path

from demo.rvo_replay import (
    build_step_replay,
    load_rvo_fixture,
    main,
    render_replay_html,
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


def test_rvo_replay_steps_match_context_sequence():
    replay = load_rvo_fixture()["demo_replay"]
    assert [step["label"] for step in replay["steps"]] == [
        "Context opened",
        "Source attached",
        "Value evidence present",
        "Cost claim rejected",
        "Implementation path present",
        "Remaining work exposed",
    ]
    assert replay["steps"][2]["events"] == [
        {
            "type": "claim_status_set",
            "claim": "claim.value_narrative",
            "status": "supported",
            "text": "RVO-style intelligence can support customer conversations around planning, prioritization, and operational risk.",
            "artifact": "artifact.value_evidence",
            "source_refs": ["source.neara_rvo"],
            "evidence_refs": ["source.neara_rvo"],
        },
        {
            "type": "artifact_status_set",
            "artifact": "artifact.value_evidence",
            "status": "present",
        },
    ]


def test_rvo_step_payloads_update_same_surfaces_over_time():
    replay = build_step_replay()
    steps = replay["steps"]
    assert len(steps) == 6
    assert all(set(step["surfaces"]) == {"coordinate", "implement", "value"} for step in steps)

    assert steps[0]["surfaces"]["coordinate"]["body"] == (
        "Context opened. Required artifacts are missing."
    )
    assert steps[0]["surfaces"]["coordinate"]["status"] == "Unresolved"
    assert steps[1]["sources"] == [
        {
            "id": "source.neara_rvo",
            "label": "Neara RVO public source",
            "locator": "demo://sources/neara-rvo",
        }
    ]
    assert steps[2]["artifact_statuses"]["artifact.value_evidence"] == "present"
    assert steps[2]["surfaces"]["value"]["claim_statuses"]["Value narrative"] == (
        "supported"
    )
    assert steps[3]["surfaces"]["value"]["claim_statuses"]["Specific cost impact claim"] == (
        "rejected"
    )
    assert steps[4]["artifact_statuses"]["artifact.integration_path"] == "present"
    assert steps[5]["primary_surface"] == "coordinate"
    assert steps[5]["changed"] == [
        "Customer system mapping is still missing",
        "ROI assumption is still missing",
        "Next executor actions are now explicit",
        "No new artifact was added in this step",
    ]


def test_step_five_kernel_next_work_matches_target():
    step = build_step_replay()["steps"][5]
    executor_actions = [
        action["contract"]
        for action in step["kernel"]["derived"]["next_work"]["executor_actions"]
    ]
    assert executor_actions == [
        "contract.customer_system_mapping",
        "contract.roi_assumption",
    ]
    assert step["surfaces"]["coordinate"]["body"] == (
        "Corus did not mark the context as solved. It derived the next accountable actions from current artifact and claim states."
    )
    assert step["surfaces"]["coordinate"]["next_executor_actions"] == [
        "Customer system mapping",
        "ROI assumption",
    ]
    assert step["surfaces"]["implement"]["body"] == (
        "Implementation path submitted. Validation blocked by customer system mapping."
    )
    assert step["surfaces"]["implement"]["validation_blockers"] == [
        "Customer system mapping"
    ]
    assert step["proof"]["supported"] == ["Value narrative"]
    assert step["proof"]["rejected"] == ["Specific cost impact claim"]
    assert step["proof"]["next_executor_actions"] == [
        "Customer system mapping",
        "ROI assumption",
    ]
    assert step["proof"]["raw"]["executor_actions"] == [
        "contract.customer_system_mapping",
        "contract.roi_assumption",
    ]


def test_rvo_replay_renders_timeline_text_not_before_after():
    output = render_replay_text()
    assert "Replay timeline" in output
    assert "Step 0 - Context opened" in output
    assert "Step 5 - Remaining work exposed" in output
    assert "Changed this step:" in output
    assert "Before:" not in output
    assert "After:" not in output
    assert (
        "Corus does not jump from unresolved to solved. It shows how context becomes clearer one event at a time."
        in output
    )


def test_rvo_replay_html_contains_timeline_cards_and_drawer():
    html = render_replay_html()
    assert "Replay timeline" in html
    assert "Coordinate" in html
    assert "Implement" in html
    assert "Value" in html
    assert "Sources" in html
    assert "Supported" in html
    assert "Rejected" in html
    assert "Kernel Output" in html
    assert "Changed this step" in html
    assert "Proof drawer" in html
    assert "View raw objects" in html


def test_rvo_replay_kernel_output_is_deterministic():
    first = build_step_replay()["steps"][5]["kernel"]
    second = build_step_replay()["steps"][5]["kernel"]
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_rvo_replay_command_prints_human_readable_timeline(capsys):
    assert main([]) == 0
    output = capsys.readouterr().out
    assert output.startswith("RVO Account Context Replay\n")
    assert "Replay timeline" in output
    assert "Step 5 - Remaining work exposed" in output


def test_rvo_replay_command_can_emit_json(capsys):
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"core_line", "framing", "object_labels", "steps", "title"}
    assert payload["steps"][4]["artifact_statuses"]["artifact.integration_path"] == (
        "present"
    )


def test_rvo_replay_command_can_write_html(tmp_path: Path, capsys):
    path = tmp_path / "rvo.html"
    assert main(["--html", str(path)]) == 0
    assert path.exists()
    assert "Wrote RVO replay page" in capsys.readouterr().out
    assert "Replay timeline" in path.read_text(encoding="utf-8")
