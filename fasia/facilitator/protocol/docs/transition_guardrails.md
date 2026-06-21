# Transition Guardrails

The facilitator protocol has three layers:

```text
1. Engine
   The objects and transitions.

2. Guardrails
   The principles that govern what is allowed to cross each transition.

3. Tests
   Boundary cases that pressure each guardrail.
```

## Core rule

Each transition has one primary guardrail.

Secondary guardrails are only used to catch common failure modes.

Do not apply all principles equally at every step.

## Engine

```text
Source
→ Candidate Origin
→ Origin
→ WorkItem
→ ExecutionProjection / MeaningProjection
→ Requirement
→ Surface
→ Outcome
→ Memory
```

## Guardrails vs transitions

`guardrails` define the vocabulary and failure modes.

`transitions` apply that vocabulary to the engine.

## Mapping

| Transition | Primary guardrail | Purpose |
|---|---|---|
| Source → Candidate Origin | Proximity | Find nearby fragments worth considering together. |
| Candidate Origin → Origin | Prägnanz | Admit the smallest adequate source whole. |
| Origin → WorkItem | Figure-ground | Extract foreground work from background context. |
| WorkItem grouping | Common fate | Group or split work by shared resolution. |
| WorkItem → Projections | Connectedness | Bind how/what and why/whom to source-supported relationships. |
| WorkItem → Requirement | Closure | Define what would count as complete. |
| WorkItem → Surface | Smallest adequate surface | Route to the least costly sufficient resolution venue. |
| Outcome → WorkItem / Memory | Continuity | Attach later evidence or state changes to the same thread. |
| Memory → recurrence | Similarity | Detect repeated patterns without proving sameness. |

## Implementation rule

Do not encode Gestalt as engine objects.

Encode it as:

```text
transition policy
prompt rules
golden boundary tests
```

If a guardrail does not produce either a prompt rule or a test case, remove it.

## Keeper

```text
The engine defines the transitions.
The guardrails define what is allowed to cross each transition.
The tests prove where the guardrails hold.
```
