# /corus:extract-work-items

Use this command when the user provides meeting notes, an email thread, a project update, or messy pre-meeting context and wants Corus to create WorkItems.

For meeting transcripts where the user wants to know what happened during the meeting, use `/corus:analyze-transcript` instead.

## Purpose

Turn vague topics and action items into closure-testable WorkItems.

A WorkItem is not a generic task. A WorkItem is unresolved work that remains open until proof and/or authority requirements are satisfied.

This command answers:

> What WorkItems exist?

## Inputs

- Source context supplied by the user.
- Existing `state/work_items.md`, when available.
- Existing `state/source_refs.md`, when available.

## Procedure

1. Identify unresolved work.
2. Merge duplicate mentions into existing WorkItems when they refer to the same unresolved question.
3. Ignore pure updates that create no unresolved work.
4. Convert vague topics into questions that can be resolved.
5. Assign closure requirements:
   - proof: evidence that would resolve the question.
   - authority: named person or role required to decide.
6. Suggest a closure surface type:
   - `async`
   - `one_on_one`
   - `meeting_with_people`
7. Return WorkItems in YAML.

## Required output shape

```yaml
work_items:
  - id: work.example_slug
    title: "Human-readable title"
    question: "What question must be resolved for this to stop coming back?"
    status: open
    closure_requirements:
      proof:
        any: []
        all: []
        none: true
      authority:
        any: []
        all: []
        none: true
    attached_people: []
    suggested_surface_type: async | one_on_one | meeting_with_people
    source_refs: []
    first_seen: YYYY-MM-DD
    last_seen: YYYY-MM-DD
    notes: "Short context note."
```

## Rules

- Do not create a WorkItem from an FYI unless it implies unresolved work.
- Do not mark a WorkItem closed unless proof or authority resolution is explicitly present.
- Do not invent people. Use names present in the source or obvious roles from the context.
- Do not over-specify org structure. Use the three closure surface types only.
- Prefer `async` when proof alone can close.
- Prefer `one_on_one` when one named person must clarify, judge, or decide.
- Prefer `meeting_with_people` when multiple people must align, decide, or provide context.

## Facilitation question

For each item ask:

> What are we trying to close?
