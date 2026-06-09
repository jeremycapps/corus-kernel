"""Agent task definitions and moment representations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Runtime verb identifiers — not declared object types.
AGENT_VERBS = frozenset({
    "agent.interpret",
    "agent.admission_report",
    "agent.admit",
    "agent.derive",
    "agent.audit",
    "agent.explain",
})

DEFAULT_ACTOR_PROFILE = "profile.corus_resolver"


@dataclass
class AgentTaskResult:
    """Result of an agent runtime action."""

    agent: str
    verb: str
    fixture_dir: Path
    outputs: dict[str, Any] = field(default_factory=dict)
    moment: dict[str, Any] | None = None


def build_moment(
    verb: str,
    obj: str,
    *,
    actor: str = DEFAULT_ACTOR_PROFILE,
    timpo: str = "timpo.runtime.0001",
    moment_id: str | None = None,
    previous: str | None = None,
) -> dict[str, Any]:
    """
    Represent an agent action as a moment using the existing moment model.

    Agents are runtime workers; moments record their occurrence without
    adding agent to the declared object model.
    """
    if verb not in AGENT_VERBS:
        raise ValueError(f"Unknown agent verb: {verb}")
    return {
        "id": moment_id or f"moment.runtime.{verb.removeprefix('agent.')}",
        "timpo": timpo,
        "actor": actor,
        "via": verb,
        "object": obj,
        "previous": previous,
    }
