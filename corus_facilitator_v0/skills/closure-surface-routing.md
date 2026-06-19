# Skill: Closure surface routing

## Definition

A ClosureSurface is where a WorkItem can be resolved.

Meetings are closure surfaces, but not every closure surface is a meeting.

## v0 surface types

Use only three modes:

- async
- one_on_one
- meeting_with_people

Do not encode org structure into surface types. Labels such as finance, leadership, publishing, or client are metadata, not types.

## async

Use async when closure can happen through proof, written confirmation, or simple recorded approval.

Default examples:

- send document
- confirm receipt
- upload payment proof
- approve in writing
- share link

Rule: Async closes with proof.

## one_on_one

Use one_on_one when one named person’s context, clarification, judgment, or authority is required.

Default examples:

- clarify a missing invoice with one person
- resolve role clarity
- discuss sensitive feedback
- get one person’s decision

Rule: One-on-one closes with a person.

## meeting_with_people

Use meeting_with_people when multiple people must align, decide, provide context, or accept proof together.

Default examples:

- approve payout plan
- revise organizational goal
- shared review session
- cross-functional tradeoff

Rule: Meetings close with people.

## Routing rule

Prefer the smallest surface that can close the WorkItem:

1. async
2. one_on_one
3. meeting_with_people

Use the smallest adequate surface, not the most important-sounding one.

## Keeper

Closure surfaces should describe the mode of closure, not the org chart.
