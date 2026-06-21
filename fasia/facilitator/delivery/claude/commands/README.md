# Claude Commands

These commands are Claude delivery affordances for the Facilitator Fasia surface.

They should route to the agent-agnostic facilitator protocol rather than redefining object semantics.

## Commands from v0 scaffold

```text
extract-work-items
analyze-transcript
prep-meeting
facilitate-meeting
record-closure
route-work-items
```

## Mapping to protocol

```text
extract-work-items
  source material → Origin / WorkItem / Projections

analyze-transcript
  source material → Outcome / Memory updates

prep-meeting
  current WorkItems / Requirements / Surfaces → facilitator prep view

facilitate-meeting
  active WorkItems / Requirements / Surfaces → live closure guidance

record-closure
  accepted proof or authority → Outcome / Memory

route-work-items
  unresolved WorkItems → smallest adequate Surface
```

## Keeper

```text
Claude commands are delivery affordances.
The facilitator protocol owns the object grammar.
```
