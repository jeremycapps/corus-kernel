"""Current object head."""

from __future__ import annotations

from dataclasses import dataclass

from timpos.moment import Moment


@dataclass(frozen=True)
class ObjectHead:
    object: str
    moment: str
    state: str

    @classmethod
    def from_moment(cls, moment: Moment) -> "ObjectHead":
        return cls(object=moment.object, moment=moment.id, state=moment.state)
