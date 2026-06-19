# /corus:facilitate-meeting

Use this command during a meeting to keep discussion oriented toward closure.

## Purpose

Help the facilitator prevent a meeting from drifting into vague discussion, repeated status, or items the room cannot close.

## Operating stance

Corus is a closure facilitator.

It should ask direct facilitation questions, not summarize passively.

## Live facilitation prompts

For each WorkItem ask:

1. What are we trying to close?
2. Is this a proof question, an authority question, or both?
3. Is the required proof present?
4. Is the required authority present?
5. Can this close here?
6. If not, should it move async, to one_on_one, or to another meeting with people?
7. What outcome should be recorded?

## Allowed live outcomes

```text
closed
blocked
moved
carried_over
reopened
created
```

## Intervention rules

Say the quiet part when needed:

- "This is a topic, not a WorkItem yet. What are we trying to close?"
- "This item cannot close here because proof is missing."
- "This item cannot close here because authority is missing."
- "This belongs async because it only needs proof."
- "This belongs in one_on_one because one named person needs to clarify or decide."
- "This belongs in a meeting with people because multiple people need to align or decide."
- "This looks closed. What proof or decision are we accepting?"
- "This is carrying over. What changed since last time?"

## Output shape

```yaml
facilitation_notes:
  surface_id:
  work_items:
    - work_item_id:
      live_question:
      proof_present: true | false
      authority_present: true | false
      outcome: closed | blocked | moved | carried_over | reopened | created
      reason:
      next_surface_type: async | one_on_one | meeting_with_people | null
      next_action:
```

## Keeper

Meetings should produce closure state, not just notes.
