# Fasia Facilitator

## Keeper

```text
Facilitator is not a separate product layer.
It is a Fasia surface for closure.
```

```text
Fasia is where Corus state becomes situated enough for someone to act.
Facilitator is the meeting-closure face of Fasia.
```

## Layer distinction

```text
Timpos remembers occurrences.
Corus coordinates derived work state.
Fasia contextualizes that state into usable surfaces.
```

The facilitator work started as a meeting-closure package, but the v0.1 object grammar and transition guardrails reveal a broader layer boundary.

The facilitator does not merely extract tasks from meetings. It binds source-grounded Corus state into a usable closure surface.

## Current relationship

```text
Source / Timpos
→ Corus coordination objects
    Origin
    WorkItem
    Requirement
    Outcome
    Memory
→ Fasia surface
    Facilitator
```

## Why facilitator belongs under Fasia

The facilitator surface decides:

```text
What becomes foreground?
What stays background?
What source span is adequate?
What work unit is being resolved?
What projection is execution?
What projection is meaning?
What requirement would count?
What is the smallest adequate surface?
What outcome should attach to memory?
```

Those are contextualization decisions.

They are not only coordination decisions.

## Current implementation

The current implementation remains in:

```text
corus_facilitator_v0_1/
```

This directory is intentionally not renamed yet.

Reason:

```text
Facilitator is the concrete surface being tested.
Fasia is the layer it may belong to.
```

Renaming too early would hide the path of discovery.

## Architecture in v0.1

```text
Origin
→ WorkItem
    ├─ ExecutionProjection: how / what
    └─ MeaningProjection: why / whom
→ Requirement
→ Surface
→ Outcome
→ Memory
```

The key correction from v0 to v0.1 is:

```text
Origin captures.
WorkItem identifies the unit.
ExecutionProjection says how / what.
MeaningProjection says why / whom.
Requirement governs resolution.
Surface routes resolution.
Outcome records transition.
Memory preserves continuity.
```

## Guardrail layer

The facilitator v0.1 package adds transition guardrails:

```text
The engine defines the transitions.
The guardrails define what is allowed to cross each transition.
The tests prove where the guardrails hold.
```

This is Fasia-like because contextualization needs rules for what is allowed to become foreground, meaning, action, requirement, surface, outcome, and memory.

## Sycophancy check

Do not collapse the architecture into:

```text
Facilitator = Fasia
```

That is too broad.

Use:

```text
Facilitator is the first concrete Fasia surface.
```

Corus still coordinates work state.

Fasia renders that state into a situated face.

Facilitator is one such face.
