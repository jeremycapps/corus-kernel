# /corus:analyze-transcript

Use this command when the user provides a meeting transcript and wants Corus to determine what changed state during the meeting.

This command is different from `/corus:extract-work-items`.

- `/corus:extract-work-items` asks: What WorkItems exist?
- `/corus:analyze-transcript` asks: What changed state in this meeting?

## Purpose

Analyze a meeting transcript as Corus, an AI closure facilitator.

Do not summarize the meeting. Extract closure state.

A WorkItem is unresolved work that can be tested for closure. Every WorkItem must have a closure question.

## Inputs

- Meeting transcript.
- Existing `state/work_items.md`, when available.
- Existing `state/closure_surfaces.md`, when available.
- Existing `state/outcomes.md`, when available.
- Existing `state/source_refs.md`, when available.

## Procedure

For each WorkItem created or discussed in the transcript:

1. Name the closure question.
2. Identify whether proof is required.
3. Identify whether authority is required.
4. Determine whether proof was present in the meeting.
5. Determine whether authority was present in the meeting.
6. Assign one outcome:
   - created
   - closed
   - blocked
   - moved
   - carried_over
   - reopened
7. If it did not close, route it to the smallest adequate closure surface:
   - async
   - one_on_one
   - meeting_with_people
8. Include transcript evidence that supports the classification.
9. Identify whether this creates, updates, closes, reopens, moves, blocks, or carries over a WorkItem.

## Existing state rule

Use existing WorkItems if provided. Merge repeated mentions into the same WorkItem instead of creating duplicates.

If a transcript mentions an already-known unresolved question, update that WorkItem rather than creating a new one.

## Required output shape

Return only YAML.

```yaml
work_items:
  - id:
    title:
    closure_question:
    status: open | closed
    proof_required:
      any: []
      all: []
      none: true | false
    authority_required:
      any: []
      all: []
      none: true | false
    proof_present: true | false
    authority_present: true | false
    outcome: created | closed | blocked | moved | carried_over | reopened
    next_surface: async | one_on_one | meeting_with_people | null
    transcript_evidence: []
    reason:

state_updates:
  new_work_items: []
  updated_work_items: []
  closure_outcomes: []
  source_refs: []
```

## Rules

- Do not mark closed unless proof or authority was explicitly accepted.
- Do not create WorkItems from pure FYIs.
- Do not preserve vague topics. Convert topics into closure questions.
- Prefer async when proof alone can close.
- Prefer one_on_one when one named person must clarify or decide.
- Prefer meeting_with_people when multiple people must align or decide.
- Prefer the smallest adequate closure surface.
- If proof or authority is unclear, mark the WorkItem blocked or carried_over instead of closed.
- Include short transcript evidence for every classification.
- Do not output a prose summary.

## Keeper

The extract prompt finds WorkItems. The transcript prompt finds closure state.
