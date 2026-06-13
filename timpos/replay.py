"""Deterministic replay over observed object states."""

from __future__ import annotations

from collections.abc import Iterable

from timpos.head import ObjectHead
from timpos.moment import Moment


def replay_to_heads(moment_log: Iterable[Moment]) -> dict[str, ObjectHead]:
    heads: dict[str, ObjectHead] = {}
    for moment in moment_log:
        heads[moment.object] = ObjectHead.from_moment(moment)
    return dict(sorted(heads.items()))


def replay_to_current_state(moment_log: Iterable[Moment]) -> dict[str, str]:
    heads = replay_to_heads(moment_log)
    return {
        object_id: head.state
        for object_id, head in heads.items()
    }
