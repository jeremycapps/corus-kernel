"""Cross-layer boundary tests."""

from __future__ import annotations

import copy
from pathlib import Path

from corus_v1.derive import derive
from demo.replay import apply_replay
from demo.rvo_replay import load_rvo_fixture
from timpos import Moment, Timpo, replay_to_current_state

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_demo_can_use_timpos_and_corus_v1():
    bundle = load_rvo_fixture()
    moments = [
        Moment.create(
            timpo=Timpo.create("2026-06-13T10:00:00Z", "model:rvo:demo"),
            object="artifact.value_evidence",
            state="present",
        )
    ]
    object_state_map = replay_to_current_state(moments)
    result = apply_replay(
        bundle,
        [
            {
                "type": "artifact_status_set",
                "artifact": "artifact.value_evidence",
                "status": object_state_map["artifact.value_evidence"],
            }
        ],
    )
    assert result["kernel"] == derive(result["stateful_bundle"])


def test_claims_only_exist_in_demo_or_product_layer():
    for root in ("timpos", "corus_v1"):
        for path in (REPO_ROOT / root).glob("*.py"):
            assert "Claim" not in path.read_text(encoding="utf-8")


def test_fasia_packet_work_stays_out_of_timpos_and_corus_v1():
    for root in ("timpos", "corus_v1"):
        for path in (REPO_ROOT / root).glob("*.py"):
            source = path.read_text(encoding="utf-8")
            assert "Surface" not in source
            assert "Fasia" not in source


def test_neara_only_exists_outside_timpos_and_corus_v1():
    for root in ("timpos", "corus_v1"):
        for path in (REPO_ROOT / root).glob("*.py"):
            assert "Neara" not in path.read_text(encoding="utf-8")


def test_demo_rendering_consumes_flow_but_does_not_change_flow():
    bundle = load_rvo_fixture()
    before = derive(bundle)
    apply_replay(
        bundle,
        [
            {
                "type": "context_opened",
                "context": "objective.rvo_customer_action",
            }
        ],
    )
    assert derive(bundle) == before


def test_claim_status_does_not_change_corus_reducer_state():
    bundle = load_rvo_fixture()
    before = derive(bundle)
    result = apply_replay(
        bundle,
        [
            {
                "type": "claim_status_set",
                "claim": "claim.demo",
                "status": "rejected",
                "text": "Demo-only claim.",
            }
        ],
    )
    assert result["kernel"] == before


def test_evidence_status_does_not_change_timpos_replay_state():
    moments = [
        Moment.create(
            timpo=Timpo.create("2026-06-13T10:00:00Z", "model:rvo:demo"),
            object="artifact.value_evidence",
            state="present",
        )
    ]
    before = replay_to_current_state(moments)
    evidence_state = {"evidence.demo": "rejected"}
    after = replay_to_current_state(copy.deepcopy(moments))
    assert evidence_state == {"evidence.demo": "rejected"}
    assert after == before
