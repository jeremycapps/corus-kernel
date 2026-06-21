# Facilitator Claude Delivery

This directory is the Claude-specific delivery package for the Facilitator Fasia surface.

It adapts the original markdown-first Corus facilitator scaffold into the new architecture:

```text
facilitator = the Fasia surface
protocol    = the agent-agnostic format
claude      = one delivery implementation
```

## Relationship to protocol

Claude delivery should use the facilitator protocol files as its source of truth:

```text
facilitator.prompt.md
facilitator.schema.yaml
facilitator.guardrails.yaml
```

The Claude package can add operating commands, task-specific skills, and workflow guidance, but it should not redefine the primitive objects.

## Contents

```text
SKILL.md
commands/
skills/
state/
examples/
```

## Keeper

```text
v0 is not obsolete.
It is the Claude-skill form of the Facilitator surface.
v0.1 is the protocol that governs it.
```
