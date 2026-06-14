"""Primitive Fasia relation object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Relation:
    """Relation is the primitive Fasia uses to make context addressable."""

    id: str
    subject: str
    predicate: str
    object: str
    state: str
    evidence: tuple[str, ...] = ()
    trace: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("id", "subject", "predicate", "object", "state"):
            field_value = getattr(self, field_name)
            if not isinstance(field_value, str) or not field_value:
                raise ValueError(f"Relation.{field_name} must be a non-empty string")
        for field_name in ("evidence", "trace"):
            field_value = getattr(self, field_name)
            if not isinstance(field_value, tuple):
                raise ValueError(f"Relation.{field_name} must be a tuple")
            for item in field_value:
                if not isinstance(item, str) or not item:
                    raise ValueError(
                        f"Relation.{field_name} must contain non-empty strings"
                    )

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "state": self.state,
        }
        if self.evidence:
            result["evidence"] = list(self.evidence)
        if self.trace:
            result["trace"] = list(self.trace)
        return result


def derive_context(
    relations: list[Relation],
    *,
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    object: Optional[str] = None,
    state: Optional[str] = None,
) -> dict[str, object]:
    """Derive a context view by selecting relations around supplied fields."""
    filters = {
        key: value
        for key, value in {
            "subject": subject,
            "predicate": predicate,
            "object": object,
            "state": state,
        }.items()
        if value is not None
    }
    selected = [
        relation
        for relation in relations
        if all(getattr(relation, key) == value for key, value in filters.items())
    ]
    selected = sorted(selected, key=lambda relation: relation.id)
    return {
        "context": {
            "selected_by": filters,
            "relations": [relation.id for relation in selected],
        },
        "relations": [relation.as_dict() for relation in selected],
    }
