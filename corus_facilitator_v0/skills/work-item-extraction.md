# Skill: WorkItem extraction

## Definition

A WorkItem is a persistent unit of unresolved work that remains open until its proof and/or authority requirements are satisfied.

A WorkItem is not simply a topic, task, note, or action item.

A good WorkItem has a question that can be resolved.

## Extraction rules

Extract a WorkItem when the source contains:

- unresolved payment, invoice, or financial follow-up
- missing document or proof
- decision that must be made
- goal that needs to be reaffirmed, revised, or evaluated
- commitment that needs confirmation
- work that keeps recurring without closure
- blocked item with named dependency

Do not extract a WorkItem for:

- pure FYI updates
- completed facts with no follow-up
- broad topics without a closure question
- brainstorming themes
- generic status unless it creates an unresolved question

## Wording normalization

Different phrasings may refer to the same WorkItem.

Example same WorkItem:

- "Ivy second invoice"
- "Confirm Ivy’s second invoice"
- "Find Ivy invoice #2"
- "Did we pay Ivy’s other invoice?"

These should merge into one WorkItem because they share the same unresolved question:

> Was Ivy’s second invoice paid, or does it still need action?

## Required fields

Every extracted WorkItem must include:

- id
- title
- question
- closure_requirements
- attached_people
- source_refs

## ID rule

Use stable, human-readable slugs for v0.

Example:

```yaml
id: work.ivy_second_invoice
```

Do not create a new id for a repeated mention of the same unresolved question.
