"""Deterministic Fasia translation edges."""

from __future__ import annotations

from dataclasses import dataclass

from fasia.context import Context

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


def translate_context(
    context: Context,
    mode: str,
    input_refs: tuple[str, ...] = (),
    output_refs: tuple[str, ...] = (),
) -> dict[str, object]:
    """Return the declared edge for one context translation mode."""
    if mode not in TRANSLATION_EDGES:
        raise ValueError(f"Unknown translation mode: {mode}")
    source_field, target_field = TRANSLATION_EDGES[mode]
    return {
        "context": context.as_dict(),
        "translation": Translation(
            mode=mode,
            source=getattr(context, source_field),
            target=getattr(context, target_field),
            input_refs=tuple(input_refs),
            output_refs=tuple(output_refs),
        ).as_dict(),
    }
