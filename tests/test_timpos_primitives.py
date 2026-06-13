"""Tests for primitive replay objects."""

from __future__ import annotations

from pathlib import Path

from timpos import Moment, Position, Timpo, replay_to_current_state, replay_to_heads

REPO_ROOT = Path(__file__).resolve().parent.parent
TIMPOS_DIR = REPO_ROOT / "timpos"


def _timpos_py_files() -> list[Path]:
    return sorted(TIMPOS_DIR.glob("*.py"))


def test_timpo_id_is_deterministic():
    first = Timpo.create("2026-06-13T10:00:00Z", Position("model:rvo:item_1"))
    second = Timpo.create("2026-06-13T10:00:00Z", "model:rvo:item_1")
    assert first.id == second.id
    assert first.t == second.t
    assert first.p == second.p


def test_moment_id_is_deterministic():
    timpo = Timpo.create("2026-06-13T10:00:00Z", "model:rvo:item_1")
    first = Moment.create(timpo=timpo, object="opaque.object", state="open")
    second = Moment.create(timpo=timpo.id, object="opaque.object", state="open")
    assert first.id == second.id


def test_moment_chain_replays_to_current_state():
    first_timpo = Timpo.create("2026-06-13T10:00:00Z", "model:rvo:item_1")
    second_timpo = Timpo.create("2026-06-13T10:01:00Z", "model:rvo:item_1")
    first = Moment.create(timpo=first_timpo, object="opaque.object", state="open")
    second = Moment.create(
        timpo=second_timpo,
        object="opaque.object",
        state="closed",
        previous=first.id,
    )
    assert replay_to_current_state([first, second]) == {"opaque.object": "closed"}


def test_object_head_exposes_latest_state():
    first = Moment.create(
        timpo=Timpo.create("2026-06-13T10:00:00Z", "model:rvo:item_1"),
        object="opaque.object",
        state="open",
    )
    second = Moment.create(
        timpo=Timpo.create("2026-06-13T10:01:00Z", "model:rvo:item_1"),
        object="opaque.object",
        state="closed",
        previous=first.id,
    )
    heads = replay_to_heads([first, second])
    assert heads["opaque.object"].moment == second.id
    assert heads["opaque.object"].state == "closed"


def test_replay_to_current_state_outputs_object_state_map():
    moments = [
        Moment.create(
            timpo=Timpo.create("2026-06-13T10:00:00Z", "model:rvo:item_1"),
            object="opaque.a",
            state="present",
        ),
        Moment.create(
            timpo=Timpo.create("2026-06-13T10:01:00Z", "model:rvo:item_2"),
            object="opaque.b",
            state="missing",
        ),
    ]
    assert replay_to_current_state(moments) == {
        "opaque.a": "present",
        "opaque.b": "missing",
    }


def test_timpos_has_no_corus_imports():
    for path in _timpos_py_files():
        assert "corus_v1" not in path.read_text(encoding="utf-8")


def test_timpos_has_no_demo_imports():
    for path in _timpos_py_files():
        assert "demo" not in path.read_text(encoding="utf-8")


def test_timpos_has_no_product_terms():
    forbidden = (
        "Objective",
        "Agent",
        "Contract",
        "Artifact",
        "Reducer",
        "Source",
        "Claim",
        "Evidence",
        "Surface",
        "Boundary",
        "Neara",
        "RAG",
        "UI",
    )
    for path in _timpos_py_files():
        source = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in source, f"{term} found in {path}"
