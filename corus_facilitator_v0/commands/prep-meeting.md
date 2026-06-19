# /corus:prep-meeting

Use this command before a meeting to determine which WorkItems can actually close there.

## Purpose

Convert a calendar event or meeting context into a closure-ready agenda.

Corus should not produce a generic agenda. It should classify WorkItems by closure fit.

## Inputs

- Meeting title.
- Meeting participants.
- Available proof or source context.
- Relevant WorkItems from `state/work_items.md`.
- Existing closure surfaces from `state/closure_surfaces.md`, when available.

## Procedure

For each candidate WorkItem:

1. Check proof requirements.
2. Check authority requirements.
3. Check whether the closure surface has the right mode:
   - `async`
   - `one_on_one`
   - `meeting_with_people`
4. Classify the item:
   - can close here
   - cannot close: missing proof
   - cannot close: missing authority
   - should be async
   - should be one_on_one
   - should move to another meeting
   - should not be discussed
5. Build the meeting agenda only from items that can close or need explicit routing.

## Output shape

```yaml
meeting_prep:
  surface:
    id:
    title:
    type:
    participants: []
    available_proof: []
  can_close:
    - work_item_id:
      reason:
      facilitation_prompt:
  cannot_close:
    - work_item_id:
      reason:
      missing_proof: []
      missing_authority: []
      recommended_route:
  should_be_async:
    - work_item_id:
      reason:
  should_be_one_on_one:
    - work_item_id:
      reason:
  should_not_discuss:
    - work_item_id:
      reason:
```

## Rules

- No closure requirement, no meeting agenda item.
- If proof is missing, say exactly what proof is missing.
- If authority is missing, say exactly who or what role is missing.
- If an item only needs proof, prefer async.
- If one person can resolve the item, prefer `one_on_one`.
- If multiple people must align or decide, keep it in `meeting_with_people`.
- Do not include broad topics without a closure question.

## Facilitation question

> Can this room close this WorkItem today?
