"""Primitive Fasia context object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Context:
    """Context is subject plus consumer, objective, value, and state."""

    subject: str
    consumer: str
    objective: str
    value: str
    state: str

    def __post_init__(self) -> None:
        for field_name in ("subject", "consumer", "objective", "value", "state"):
            field_value = getattr(self, field_name)
            if not isinstance(field_value, str) or not field_value:
                raise ValueError(f"Context.{field_name} must be a non-empty string")

    def as_dict(self) -> dict[str, str]:
        return {
            "subject": self.subject,
            "consumer": self.consumer,
            "objective": self.objective,
            "value": self.value,
            "state": self.state,
        }
