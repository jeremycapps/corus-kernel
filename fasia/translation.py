"""Deterministic Fasia translation over relations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fasia.relation import Relation, derive_context

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
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    object: Optional[str] = None,
    state: Optional[str] = None,
    input_refs: tuple[str, ...] = (),
    output_refs: tuple[str, ...] = (),
) -> dict[str, object]:
    """Return one declared translation edge over a derived relation context."""
    if mode not in TRANSLATION_EDGES:
        raise ValueError(f"Unknown translation mode: {mode}")
    source, target = TRANSLATION_EDGES[mode]
    context = derive_context(
        relations,
        subject=subject,
        predicate=predicate,
        object=object,
        state=state,
    )
    return {
        **context,
        "translation": Translation(
            mode=mode,
            source=source,
            target=target,
            input_refs=tuple(input_refs),
            output_refs=tuple(output_refs),
        ).as_dict(),
    }
