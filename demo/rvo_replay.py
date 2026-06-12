"""Renderable RVO-style replay around the frozen Corus v1 kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from demo.replay import apply_replay

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "rvo"

INITIAL_CLAIMS = [
    {
        "id": "claim.value_narrative_supported",
        "status": "admitted",
        "text": "RVO risk intelligence supports a customer-specific value narrative.",
        "artifact": "artifact.value_evidence",
        "evidence_refs": ["source.rvo_public_brief"],
    },
    {
        "id": "claim.unsupported_cost_impact",
        "status": "candidate",
        "text": "Specific cost impact is not supported by admitted evidence.",
        "artifact": "artifact.roi_assumption",
        "evidence_refs": [],
    },
]

REPLAY_EVENTS = [
    {
        "type": "context_opened",
        "context": "objective.rvo_customer_action",
        "label": "Director opens RVO customer action context",
    },
    {
        "type": "source_ref_added",
        "source": "source.rvo_public_brief",
        "label": "RVO public planning brief",
        "locator": "demo://sources/rvo-public-brief",
    },
    {
        "type": "claim_status_set",
        "claim": "claim.unsupported_cost_impact",
        "status": "rejected",
        "text": "Do not claim specific cost impact until customer evidence is admitted.",
        "artifact": "artifact.roi_assumption",
        "evidence_refs": [],
    },
    {
        "type": "artifact_status_set",
        "artifact": "artifact.integration_path",
        "status": "present",
    },
]


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_rvo_fixture(fixture_dir: Path = FIXTURE_DIR) -> dict[str, Any]:
    """Load the demo RVO fixture in the same shape consumed by corus_v1."""
    return {
        "project": _read_yaml(fixture_dir / "project.yaml"),
        "agents": _read_yaml(fixture_dir / "agents.yaml"),
        "objectives": _read_yaml(fixture_dir / "objectives.yaml"),
        "contracts": _read_yaml(fixture_dir / "contracts.yaml"),
        "artifacts": _read_yaml(fixture_dir / "artifacts.yaml"),
        "demo_surfaces": _read_yaml(fixture_dir / "surfaces.yaml")["surfaces"],
    }


def _artifact_status(payload: dict[str, Any], artifact_id: str) -> str:
    return payload["state"]["artifact_statuses"][artifact_id]


def _claim_status(payload: dict[str, Any], claim_id: str) -> str:
    for claim in payload["state"]["claims"]:
        if claim["id"] == claim_id:
            return claim["status"]
    return "missing"


def _human_status(status: str) -> str:
    return {
        "expected_missing": "missing",
        "present": "present",
        "validated": "supported",
        "rejected": "rejected",
    }.get(status, status)


def _surface_config(payload: dict[str, Any], surface: str) -> dict[str, Any]:
    return payload["demo_surfaces"][surface]


def _coordinate_line(payload: dict[str, Any], phase: str) -> str:
    config = _surface_config(payload, "coordinate")
    coordinate = payload["surfaces"]["coordinate"]
    if phase == "before":
        return config["before"]
    next_actions = coordinate["next_executor_actions"] + coordinate["next_consumer_actions"]
    return f"{config['after_next_action_prefix']} {', '.join(next_actions)}"


def _implement_line(payload: dict[str, Any], phase: str) -> str:
    config = _surface_config(payload, "implement")
    if phase == "before":
        return config["before"]
    artifacts = config["artifacts"]
    values: dict[str, str] = {}
    for key, artifact in artifacts.items():
        values[key] = artifact["label"]
        values[f"{key}_status"] = _human_status(_artifact_status(payload, artifact["id"]))
    return config["after_template"].format(**values)


def _value_line(payload: dict[str, Any], phase: str) -> str:
    config = _surface_config(payload, "value")
    if phase == "before":
        return config["before"]
    values: dict[str, str] = {}
    for key, artifact in config.get("artifacts", {}).items():
        values[key] = artifact["label"]
        values[f"{key}_status"] = _human_status(_artifact_status(payload, artifact["id"]))
    for key, claim in config.get("claims", {}).items():
        values[key] = claim["label"]
        values[f"{key}_status"] = _claim_status(payload, claim["id"])
    return config["after_template"].format(**values)


def render_replay_text(before: dict[str, Any], after: dict[str, Any]) -> str:
    """Render the human-facing before/after demo transcript."""
    events = [
        f"  - {event['type']}: {event.get('label') or event.get('claim') or event.get('artifact') or event.get('source')}"
        for event in after["state"]["event_log"]
    ]
    lines = [
        "RVO Customer Action Replay",
        "",
        "Replay sequence:",
        *events,
        "",
        "Before:",
        f"  {_coordinate_line(before, 'before')}",
        f"  {_implement_line(before, 'before')}",
        f"  {_value_line(before, 'before')}",
        "",
        "After:",
        f"  {_coordinate_line(after, 'after')}",
        f"  {_implement_line(after, 'after')}",
        f"  {_value_line(after, 'after')}",
    ]
    return "\n".join(lines) + "\n"


def build_replay() -> tuple[dict[str, Any], dict[str, Any]]:
    """Build before/after replay payloads."""
    bundle = load_rvo_fixture()
    before = apply_replay(bundle, [], claims=INITIAL_CLAIMS)
    after = apply_replay(bundle, REPLAY_EVENTS, claims=INITIAL_CLAIMS)
    before["demo_surfaces"] = copy_fixture_surfaces(bundle)
    after["demo_surfaces"] = copy_fixture_surfaces(bundle)
    return before, after


def copy_fixture_surfaces(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return render-only surface bindings from the demo fixture."""
    return json.loads(json.dumps(bundle["demo_surfaces"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m demo.rvo_replay",
        description="Render the RVO demo replay",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit before/after replay payloads as JSON",
    )
    args = parser.parse_args(argv)

    before, after = build_replay()
    if args.json:
        print(json.dumps({"before": before, "after": after}, indent=2, sort_keys=True))
    else:
        print(render_replay_text(before, after), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
