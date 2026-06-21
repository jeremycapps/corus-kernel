# Corus Facilitator v0.1

Corus Facilitator v0.1 is the YAML-first version of the facilitator and the first concrete candidate Fasia surface.

The existing `corus_facilitator_v0/` markdown package remains the research scaffold. It helped discover the facilitation behavior, command split, and closure discipline.

This version moves the center of gravity from command prompts to object shapes, transition guardrails, and golden boundary tests.

## Layer position

```text
Timpos remembers occurrences.
Corus coordinates derived work state.
Fasia contextualizes that state into usable surfaces.
```

Facilitator is not the whole Fasia layer.

Facilitator is the meeting-closure face of Fasia.

```text
Facilitator is a Fasia surface for closure.
```

## Core principle

```text
Prompts tell the model what to do.
Object shapes tell the model what counts.
```

## Architecture

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

## Locked definitions

### Origin

The minimum auditable source span from which a WorkItem and its projections can be derived.

Origin anchors source reality.

### WorkItem

The derived unit of work anchored to an Origin. It identifies the thing being resolved and carries current state.

WorkItem anchors the unit of work.

### ExecutionProjection

The execution reading of the WorkItem.

```text
how / what
```

### MeaningProjection

The meaning reading of the same WorkItem.

```text
why / whom
```

### Requirement

What must be true for the WorkItem to resolve.

### Surface

The smallest adequate venue where resolution can happen.

Allowed v0.1 surface types:

```text
async
one_on_one
meeting_with_people
```

### Outcome

The state transition that happened to the WorkItem.

Allowed v0.1 outcomes:

```text
created
resolved
blocked
moved
carried_over
reopened
```

### Memory

The persistent continuity of the WorkItem across time.

## Why this exists

The markdown-first v0 flattened the facilitation chain into convenient command outputs. That was useful for testing behavior, but it made `WorkItem` absorb requirements, routing, outcomes, evidence, people, dates, and notes.

v0.1 separates the primitive objects from the facilitator view.

The key correction is:

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

The guardrail layer keeps the engine from drifting as source material becomes context, action, resolution, and memory.

```text
The engine defines the transitions.
The guardrails define what is allowed to cross each transition.
The tests prove where the guardrails hold.
```

Guardrails are not engine objects. They are transition policy, prompt rules, and golden boundary tests.

## Package structure

```text
corus_facilitator_v0_1/
├── README.md
├── corus_facilitator.prompt.md
├── corus_facilitator.schema.yaml
├── corus_facilitator.guardrails.yaml
├── docs/
│   └── transition_guardrails.md
├── examples/
│   ├── h1-review.input.txt
│   └── h1-review.output.yaml
└── tests/
    └── golden/
        └── guardrail_cases.yaml
```

## Usage

1. Give the model `corus_facilitator.prompt.md` as the initial instruction.
2. Give the model `corus_facilitator.schema.yaml` as the required object grammar.
3. Give the model `corus_facilitator.guardrails.yaml` as the transition policy.
4. Provide meeting notes, transcripts, email threads, Slack threads, or other source material.
5. Ask for YAML output only.

## Keeper

```text
Origin anchors source reality.
WorkItem anchors the unit of work.
Projections preserve execution and meaning without bloating the WorkItem.
```

```text
Same Origin. Same WorkItem. Different projections.
```

```text
Facilitator is a Fasia surface for closure.
```
