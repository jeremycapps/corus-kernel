"""Deterministic Fasia translation over relation paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fasia.relation import Relation, derive_relation_paths

TRANSLATION_EDGES: dict[str, tuple[str, str]] = {
    "discovery": ("consumer", "objective"),
    "strategy": ("objective", "value"),
    "product": ("value", "consumer"),
}


@dataclass(frozen=True)
class Translation:
    mode: str
    source: str
    target: str
    input_refs: tuple[str, ...] = ()
    output_refs: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "source": self.source,
            "target": self.target,
            "input_refs": list(self.input_refs),
            "output_refs": list(self.output_refs),
        }


def translate_relations(
    relations: list[Relation],
    mode: str,
    *,
    admitted_sources: tuple[str, ...],
    active_objectives: tuple[str, ...],
    node_states: Optional[dict[str, str]] = None,
    corus_blocked_artifacts: tuple[str, ...] = (),
    input_refs: tuple[str, ...] = (),
    output_refs: tuple[str, ...] = (),
) -> dict[str, object]:
    """Return one translation edge over derived relation paths."""
    if mode not in TRANSLATION_EDGES:
        raise ValueError(f"Unknown translation mode: {mode}")
    source, target = TRANSLATION_EDGES[mode]
    paths = derive_relation_paths(
        relations,
        admitted_sources=admitted_sources,
        active_objectives=active_objectives,
        node_states=node_states,
        corus_blocked_artifacts=corus_blocked_artifacts,
    )
    return {
        "relations": [
            relation.as_dict()
            for relation in sorted(relations, key=lambda item: item.id)
        ],
        "derived_relations": paths,
        "translation": Translation(
            mode=mode,
            source=source,
            target=target,
            input_refs=tuple(input_refs),
            output_refs=tuple(output_refs),
        ).as_dict(),
    }
