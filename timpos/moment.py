"""Observed object state at a time-position address."""

from __future__ import annotations

from dataclasses import dataclass

from timpos.timpo import Timpo
from timpos.util import deterministic_id


@dataclass(frozen=True)
class Moment:
    id: str
    timpo: str
    object: str
    state: str
    previous: str | None = None

    @classmethod
    def create(
        cls,
        *,
        timpo: str | Timpo,
        object: str,
        state: str,
        previous: str | None = None,
    ) -> "Moment":
        timpo_id = timpo.id if isinstance(timpo, Timpo) else timpo
        payload = {
            "timpo": timpo_id,
            "object": object,
            "state": state,
            "previous": previous,
        }
        item_id = deterministic_id("moment", payload)
        return cls(
            id=item_id,
            timpo=timpo_id,
            object=object,
            state=state,
            previous=previous,
        )
