# Fasia Facilitator

## Keeper

```text
Facilitator is not a separate product layer.
It is a Fasia surface for closure.
```

```text
Facilitator is the Fasia surface.
Protocol is the agent-agnostic format.
Claude is one delivery implementation.
```

## Layer distinction

```text
Timpos remembers occurrences.
Corus coordinates derived work state.
Fasia contextualizes that state into usable surfaces.
```

The facilitator work started as a meeting-closure package, but the object grammar and transition guardrails reveal a broader layer boundary.

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
        protocol
        delivery/claude
```

## Active implementation

```text
fasia/facilitator/
├── README.md
├── protocol/
│   ├── README.md
│   ├── facilitator.prompt.md
│   ├── facilitator.schema.yaml
│   ├── facilitator.guardrails.yaml
│   ├── docs/
│   ├── examples/
│   └── tests/
└── delivery/
    └── claude/
        ├── README.md
        ├── SKILL.md
        ├── commands/
        ├── skills/
        ├── state/
        └── examples/
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

## Protocol

The protocol is agent-agnostic.

It contains:

```text
object grammar
prompt behavior
transition guardrails
examples
golden boundary tests
```

The protocol should be usable across Claude, ChatGPT, Codex-style agents, custom API workers, UI flows, and other agentic delivery forms.

## Claude delivery

Claude delivery is one implementation of the facilitator surface.

It can provide commands, skill modules, workflow guidance, and human-facing operating discipline.

It should not redefine the protocol objects.

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

The key correction from the discovery scaffolds is:

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
