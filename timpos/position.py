"""Opaque position locator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("position value must be a non-empty string")

    def __str__(self) -> str:
        return self.value
