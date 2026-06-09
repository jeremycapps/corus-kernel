"""Derive Agent — derive context from admitted declared objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from corus_kernel.derive import derive_context
from corus_kernel.loader import DERIVE_BUNDLE_FILES, INTERPRET_CANDIDATE_FILES

from corus_agents.tasks import AgentTaskResult, build_moment
from corus_agents.workflow import derive_blocked_reason

DERIVE_OUTPUT = "derive.output.json"


def run(
    fixture_dir: Path,
    *,
    boundary_id: str | None = None,
    output_path: Path | None = None,
) -> AgentTaskResult:
    """
    Derive context from admitted YAML only.

    Never reads candidate files — delegates to corus_kernel.derive.
    """
    fixture_dir = Path(fixture_dir)
    blocked = derive_blocked_reason(fixture_dir)
    if blocked:
        raise RuntimeError(blocked)

    _assert_derive_reads_admitted_only()

    output = derive_context(fixture_dir, boundary_id=boundary_id)
    out_path = output_path or (fixture_dir / DERIVE_OUTPUT)
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return AgentTaskResult(
        agent="derive",
        verb="agent.derive",
        fixture_dir=fixture_dir,
        outputs={
            "derive_output": str(out_path),
            "coordination": output["derived"]["context_state"]["coordination"],
            "content_hash": output["hashes"]["content"],
        },
        moment=build_moment(
            "agent.derive",
            str(out_path),
            moment_id="moment.runtime.derive",
        ),
    )


def _assert_derive_reads_admitted_only() -> None:
    for name in INTERPRET_CANDIDATE_FILES:
        if name.endswith(".yaml") and "candidate" not in name:
            raise AssertionError(f"Unexpected candidate file name: {name}")
    for filename in DERIVE_BUNDLE_FILES.values():
        if "candidate" in filename:
            raise AssertionError(f"Derive must not load candidate file: {filename}")


def load_output(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
