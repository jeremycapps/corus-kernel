"""Primitive Fasia relation graph objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

PATH_OPEN = "open"
PATH_CLOSED = "closed"

TARGET_OBJECT = "object"
TARGET_SUBJECT = "subject"
TARGET_TYPES = (TARGET_OBJECT, TARGET_SUBJECT)

NODE_USABLE_STATES = ("present", "validated", "usable", "reachable", "admitted")
NODE_UNUSABLE_STATES = ("missing", "expected_missing", "rejected", "unusable")

DERIVED_LABELS = {
    (TARGET_OBJECT, PATH_OPEN): "enables",
    (TARGET_OBJECT, PATH_CLOSED): "blocks",
    (TARGET_SUBJECT, PATH_OPEN): "affects",
    (TARGET_SUBJECT, PATH_CLOSED): "risks",
}


@dataclass(frozen=True)
class Target:
    """Destination node plus context typing."""

    type: str
    id: str
    label: str

    def __post_init__(self) -> None:
        if self.type not in TARGET_TYPES:
            raise ValueError("Target.type must be object or subject")
        for field_name in ("id", "label"):
            field_value = getattr(self, field_name)
            if not isinstance(field_value, str) or not field_value:
                raise ValueError(f"Target.{field_name} must be a non-empty string")

    def as_dict(self) -> dict[str, str]:
        return {
            "type": self.type,
            "id": self.id,
            "label": self.label,
        }


@dataclass(frozen=True)
class Relation:
    """Authored contextual edge declaration."""

    id: str
    initiator: str
    target: Target
    sources: tuple[str, ...]
    objectives: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("id", "initiator"):
            field_value = getattr(self, field_name)
            if not isinstance(field_value, str) or not field_value:
                raise ValueError(f"Relation.{field_name} must be a non-empty string")
        if not isinstance(self.target, Target):
            raise ValueError("Relation.target must be a Target")
        _validate_refs("Relation.sources", self.sources, "source.")
        _validate_refs("Relation.objectives", self.objectives, "objective.")

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "initiator": self.initiator,
            "target": self.target.as_dict(),
            "sources": list(self.sources),
            "objectives": list(self.objectives),
        }


@dataclass(frozen=True)
class DerivedRelation:
    """Computed path condition for an authored relation."""

    relation: str
    path: str
    label: str
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.relation, str) or not self.relation:
            raise ValueError("DerivedRelation.relation must be a non-empty string")
        if self.path not in (PATH_OPEN, PATH_CLOSED):
            raise ValueError("DerivedRelation.path must be open or closed")
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("DerivedRelation.label must be a non-empty string")
        if not isinstance(self.reasons, tuple):
            raise ValueError("DerivedRelation.reasons must be a tuple")
        for reason in self.reasons:
            if not isinstance(reason, str) or not reason:
                raise ValueError(
                    "DerivedRelation.reasons must contain non-empty strings"
                )

    def as_dict(self) -> dict[str, object]:
        return {
            "relation": self.relation,
            "path": self.path,
            "label": self.label,
            "reasons": list(self.reasons),
        }


def derive_relation_paths(
    relations: Sequence[Relation],
    *,
    admitted_sources: Sequence[str],
    active_objectives: Sequence[str],
    node_states: Optional[Mapping[str, str]] = None,
    corus_blocked_artifacts: Sequence[str] = (),
) -> list[dict[str, object]]:
    """Derive open or closed path state for each authored relation."""
    admitted_source_set = set(admitted_sources)
    active_objective_set = set(active_objectives)
    node_states = node_states or {}
    blocked_artifact_set = set(corus_blocked_artifacts)

    derived = []
    for relation in sorted(relations, key=lambda item: item.id):
        reasons = _closed_reasons(
            relation,
            admitted_sources=admitted_source_set,
            active_objectives=active_objective_set,
            node_states=node_states,
            corus_blocked_artifacts=blocked_artifact_set,
        )
        path = PATH_CLOSED if reasons else PATH_OPEN
        derived.append(
            DerivedRelation(
                relation=relation.id,
                path=path,
                label=DERIVED_LABELS[(relation.target.type, path)],
                reasons=tuple(reasons),
            ).as_dict()
        )
    return derived


def _closed_reasons(
    relation: Relation,
    *,
    admitted_sources: set[str],
    active_objectives: set[str],
    node_states: Mapping[str, str],
    corus_blocked_artifacts: set[str],
) -> list[str]:
    reasons: list[str] = []
    if any(source not in admitted_sources for source in relation.sources):
        reasons.append("source_not_admitted")
    if not any(objective in active_objectives for objective in relation.objectives):
        reasons.append("objective_out_of_scope")
    initiator_reason = _node_reason(relation.initiator, "initiator", node_states)
    if initiator_reason:
        reasons.append(initiator_reason)
    target_reason = _node_reason(relation.target.id, "target", node_states)
    if target_reason:
        reasons.append(target_reason)
    if relation.target.id in corus_blocked_artifacts:
        reasons.append("target_blocked_by_corus_readiness")
    return reasons


def _node_reason(
    node_id: str,
    label: str,
    node_states: Mapping[str, str],
) -> Optional[str]:
    state = node_states.get(node_id)
    if state in NODE_UNUSABLE_STATES:
        return f"{label}_unusable"
    return None


def _validate_refs(field_name: str, refs: tuple[str, ...], prefix: str) -> None:
    if not isinstance(refs, tuple) or not refs:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    for ref in refs:
        if not isinstance(ref, str) or not ref:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if not ref.startswith(prefix):
            raise ValueError(f"{field_name} entries must start with {prefix}")
