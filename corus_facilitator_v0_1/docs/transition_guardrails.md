# Transition Guardrails

Corus Facilitator v0.1 has three layers:

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

The engine defines the transitions.

The guardrails define what is allowed to cross each transition.

The tests prove where the guardrails hold.

## Guardrails vs transitions

The guardrails file has two top-level sections:

```yaml
guardrails:
  pragnanz:
  figure_ground:
  common_fate:
  connectedness:
  closure:
  continuity:
  similarity:
  proximity:
  smallest_adequate_surface:

transitions:
  source_to_candidate_origin:
  candidate_origin_to_origin:
  origin_to_work_item:
  work_item_grouping:
  work_item_to_projections:
  work_item_to_requirement:
  work_item_to_surface:
  outcome_to_work_item_memory:
  memory_to_recurrence:
```

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

## Primary guardrails

### Proximity

Proximity proposes Candidate Origins.

Nearby fragments may belong together, but proximity does not admit an Origin.

Failure prevented:

```text
isolated fragment extraction
missing nearby context
missing local referents
```

### Prägnanz

Prägnanz admits Origins.

Corus definition:

```text
The smallest source span that can justify the same WorkItem across both execution and meaning.
```

Failure prevented:

```text
underbounded Origins
overbounded Origins
topic-as-Origin
quote-without-force
```

### Figure-ground

Figure-ground extracts WorkItems.

It separates foreground work pressure from background context inside an Origin.

Failure prevented:

```text
background context becoming fake work
missed foreground unresolved work
too many tasks from one source event
```

### Common fate

Common fate groups or splits WorkItems.

Fragments belong to one WorkItem only when they resolve together.

Failure prevented:

```text
false merge
false split
grouping by similarity alone
```

### Connectedness

Connectedness binds projections.

The model may derive how/what and why/whom only from relationships supported by the source.

Failure prevented:

```text
invented how
invented what
invented why
invented whom
meaning detached from source
```

### Closure

Closure defines Requirements.

Here, closure means: what would complete the open WorkItem shape?

Failure prevented:

```text
vague done criteria
inflated requirements
marking closed without proof or authority
```

### Smallest adequate surface

Smallest adequate surface routes WorkItems.

Use:

```text
async               when proof alone can resolve
one_on_one          when one named person must clarify or decide
meeting_with_people when multiple people must align, decide, or provide context
```

Failure prevented:

```text
over-meeting
under-routing
routing authority decisions to async
routing multi-person alignment to one_on_one
```

### Continuity

Continuity attaches Outcomes to WorkItems and Memory.

Later evidence should attach to an existing WorkItem only when it continues the same thread.

Failure prevented:

```text
lost closures
duplicate WorkItems
evidence attached to the wrong thread
creating new work from resolution evidence
```

### Similarity

Similarity informs Memory recurrence.

It detects repeated patterns, but it does not prove sameness.

Failure prevented:

```text
merging similar but distinct work
missing repeated operational patterns
treating recurrence as identity
```

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
