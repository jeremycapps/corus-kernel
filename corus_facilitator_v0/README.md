# Corus Facilitator v0

Corus Facilitator v0 is a Claude knowledge-worker style markdown package for AI-assisted meeting facilitation.

It is not an AI note-taker, agenda generator, calendar replacement, or task manager. It helps a facilitator turn meeting context into closure-ready work.

## Core thesis

Meeting notes preserve discussion. Closure preserves accomplishment.

Corus helps teams answer one question before, during, and after a meeting:

> What can this conversation actually close?

## Core logic

```text
WorkItem -> ClosureRequirement -> ClosureSurface -> ClosureOutcome -> ClosureMemory
```

- **WorkItem**: unresolved work that can be tested for closure.
- **ClosureRequirement**: proof and/or authority needed to close the WorkItem.
- **ClosureSurface**: where closure can happen: `async`, `1:1`, or `meeting_with_people`.
- **ClosureOutcome**: what happened to the WorkItem: `created`, `closed`, `blocked`, `moved`, `carried_over`, or `reopened`.
- **ClosureMemory**: persistent record of what closed, what moved, what stayed blocked, and why.

## Keeper rules

- No closure requirement, no meeting agenda item.
- Async closes with proof.
- 1:1 closes with a person.
- Meetings close with people.
- Claude handles ambiguity. Corus preserves closure state.
- Use Claude to find the WorkItems. Use Corus to remember whether they close.

## Package structure

```text
corus_facilitator_v0/
├── README.md
├── commands/
│   ├── extract-work-items.md
│   ├── prep-meeting.md
│   ├── facilitate-meeting.md
│   ├── record-closure.md
│   └── route-work-items.md
├── skills/
│   ├── work-item-extraction.md
│   ├── closure-requirements.md
│   ├── closure-surface-routing.md
│   ├── facilitation-discipline.md
│   └── closure-memory.md
├── state/
│   ├── work_items.md
│   ├── closure_surfaces.md
│   ├── closure_outcomes.md
│   └── source_refs.md
└── examples/
    └── h1-review-finance-admin.md
```

## v0 usage

1. Paste meeting notes into `/extract-work-items`.
2. Store the generated WorkItems in `state/work_items.md`.
3. Use `/prep-meeting` before a meeting to decide what can close there.
4. Use `/facilitate-meeting` during the meeting to keep the room oriented toward closure.
5. Use `/record-closure` after the meeting to update closure memory.
