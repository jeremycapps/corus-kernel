"""Time-position observation address."""

from __future__ import annotations

from dataclasses import dataclass

from timpos.position import Position
from timpos.util import deterministic_id


@dataclass(frozen=True)
class Timpo:
    id: str
    t: str
    p: str

    @classmethod
    def create(cls, t: str, p: str | Position) -> "Timpo":
        position = str(p)
        item_id = deterministic_id("timpo", {"t": t, "p": position})
        return cls(id=item_id, t=t, p=position)
