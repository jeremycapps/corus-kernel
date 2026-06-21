# Fasia Facilitator

Facilitator is a Fasia surface for closure.

```text
Fasia
└── facilitator
    ├── protocol
    └── delivery
        └── claude
```

## Layer distinction

```text
Timpos remembers occurrences.
Corus coordinates derived work state.
Fasia contextualizes that state into usable surfaces.
```

The facilitator surface turns source-grounded work state into a closure-oriented face:

```text
Source material
→ Origin
→ WorkItem
→ ExecutionProjection / MeaningProjection
→ Requirement
→ Surface
→ Outcome
→ Memory
```

## Directory roles

```text
protocol/
  Agent-agnostic facilitator format.
  Holds the prompt, schema, guardrails, examples, and golden boundary cases.

 delivery/claude/
  Claude-specific delivery package.
  Holds the markdown command/skill scaffold discovered in corus_facilitator_v0.
```

## Keeper

```text
Facilitator is the Fasia surface.
Protocol is the agent-agnostic format.
Claude is one delivery implementation.
```
