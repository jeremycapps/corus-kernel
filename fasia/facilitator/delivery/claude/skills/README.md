# Claude Skill Modules

These skill modules come from the v0 markdown-first facilitator scaffold.

They are delivery guidance for Claude, not engine objects.

## Skill modules from v0 scaffold

```text
work-item-extraction
closure-requirements
closure-surface-routing
facilitation-discipline
closure-memory
```

## Protocol ownership

The agent-agnostic protocol owns the primitive object model:

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

Claude skill modules may explain how to operate those objects in conversation, but should not add new primitive fields or object types.
