# /corus:record-closure

Use this command after a meeting, async exchange, or one_on_one to update closure memory.

## Purpose

Record what happened to each WorkItem so Corus can remember what was accomplished.

Meeting notes remember what was said. Closure remembers what was accomplished.

## Inputs

- WorkItems discussed or routed.
- Closure surface where the attempt happened.
- Proof accepted, authority decision made, or reason closure failed.
- Existing `state/work_items.md` and `state/outcomes.md`.

## Allowed outcomes

```text
created
closed
blocked
moved
carried_over
reopened
```

## Output shape

```yaml
outcomes:
  - id: outcome.example
    work_item_id:
    surface_id:
    outcome: closed | blocked | moved | carried_over | reopened | created
    proof_accepted: []
    authority_accepted: []
    missing_proof: []
    missing_authority: []
    reason:
    next_surface_type: async | one_on_one | meeting_with_people | null
    next_surface_id:
    timestamp:
```

## State update rules

- If outcome is `closed`, update WorkItem status to `closed` only when proof and/or authority resolution is explicitly named.
- If outcome is `blocked`, preserve status as `open` and record the blocker.
- If outcome is `moved`, preserve status as `open` and record the next closure surface.
- If outcome is `carried_over`, preserve status as `open` and increment carryover in derived metrics later.
- If outcome is `reopened`, status becomes `open` and the previous closure proof should be referenced.
- If outcome is `created`, create a new WorkItem or candidate WorkItem.

## Rules

- Do not infer closure from discussion alone.
- Do not mark closed without accepted proof or authority.
- Record why closure failed when it failed.
- Prefer concise closure memory over full meeting notes.

## Keeper

Closure is not what people discussed. Closure is what the meeting accomplished.
