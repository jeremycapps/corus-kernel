# Skill: Closure memory

## Definition

Closure memory is the preserved record of what was accomplished across surfaces and time.

Meeting notes remember what was said.
Closure remembers what was accomplished.

## What closure memory tracks

For each WorkItem, preserve:

- when it first appeared
- where closure was attempted
- who or what was required
- what proof was missing
- what authority was missing
- whether it closed, moved, blocked, reopened, or carried over
- what proof or authority finally closed it

## Closure outcomes

Allowed v0 outcomes:

- created
- closed
- blocked
- moved
- carried_over
- reopened

## Rules

- Do not mark a WorkItem closed from discussion alone.
- Closed requires accepted proof, accepted authority, or both according to the WorkItem’s closure requirements.
- Blocked means the WorkItem remains open because something required is missing.
- Moved means the WorkItem remains open but has a better closure surface.
- Carried over means the WorkItem remains open and returns to a future surface without meaningful state change.
- Reopened means a previously closed WorkItem is open again because the accepted closure was invalidated or new unresolved context appeared.

## Future metrics enabled

- time to close
- carryover count
- missing proof count
- missing authority count
- reopened count
- closure rate by surface
- closure rate by required person
- repeated non-closure

## Keeper

Closure remembers what was accomplished.
