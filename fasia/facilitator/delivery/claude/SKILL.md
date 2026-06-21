# Facilitator Claude Skill

Use this skill when the user wants Claude-style help facilitating closure from meeting notes, transcripts, email threads, Slack threads, or other work conversations.

This skill is a delivery layer for the Facilitator Fasia surface.

It should use the agent-agnostic protocol as the source of truth:

```text
facilitator.prompt.md
facilitator.schema.yaml
facilitator.guardrails.yaml
```

## What this skill does

It helps a human facilitator:

```text
find closure-ready work
prepare a meeting
keep discussion oriented toward closure
route unresolved work
record outcomes
preserve closure memory
```

## What this skill is not

It is not:

```text
a note-taker
an agenda generator
a task manager
a transcript summarizer
```

## Operating rule

Use Claude-specific commands and workflow guidance only as delivery affordances.

Do not redefine the protocol objects.

The protocol owns:

```text
Origin
WorkItem
ExecutionProjection
MeaningProjection
Requirement
Surface
Outcome
Memory
```

## Keeper

```text
Facilitator is the surface.
Protocol is the agent-agnostic format.
Claude is one delivery implementation.
```
