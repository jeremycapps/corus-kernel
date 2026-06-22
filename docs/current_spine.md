# Current Spine

This document records the current locked Corus architecture spine.

## Role spine

```text
Libera catalogs.
Corus orchestrates.
Facia facilitates.
Timpos registers.
```

## Role meanings

```text
Libera = librarian
Corus = orchestrator
Facia = facilitator
Timpos = registrar
```

Libera catalogs source-grounded candidates.

Corus admits, coordinates, routes, and derives state.

Facia turns coordinated state into surfaces, priorities, claims, and next actions.

Timpos records official events, transitions, and replayable history.

## Engine spine

```text
source
→ catalog
→ admission
→ registration
→ coordination
→ facilitation
→ action
→ registration
```

## Protocol principle

```text
Protocol owns the rules.
Roles configure the agents.
Handoffs configure the transitions.
Delivery adapts the protocol to Claude, ChatGPT, Codex, API, or UI.
```

Roles are not the top-level abstraction. Roles are configuration files that run through a shared protocol and agent runtime.

## YAML constraint

```text
Prompts guide.
YAML constrains.
Gestalt guards.
Timpos records.
```

Every agent role should have a role configuration that defines what it may receive, produce, refuse, and hand off.

Every handoff should have a handoff configuration that defines what object moves, which validators apply, what the receiver may do, and whether Timpos must register the transition.

## Handoff principle

A handoff is not simply one agent passing text to another agent.

A handoff is:

```text
A typed object
moving between two protocol roles
under explicit validator rules
with receiver permissions
and registration requirements.
```

## Gestalt guardrail layer

Gestalt principles validate role handoffs. They are not philosophy objects and they are not engine objects. They are transition guardrails.

```text
Source → Candidate Origin
  Guardrail: Proximity

Candidate Origin → Origin
  Guardrail: Prägnanz

Origin → WorkItem
  Guardrail: Figure-ground

WorkItem grouping / splitting
  Guardrail: Common fate

WorkItem → ExecutionProjection / MeaningProjection
  Guardrail: Connectedness

WorkItem → Requirement
  Guardrail: Closure

Catalog Packet → Corus Admission
  Guardrail: Similarity + Connectedness

Coordination State → Facia Surface
  Guardrail: Figure-ground + Smallest adequate surface

Action / Evidence → Timpos Registration
  Guardrail: Continuity
```

## Recommended protocol format

```text
protocol/
  README.md
  prompt.md
  schema.yaml
  guardrails.yaml

  roles/
    libera.yaml
    corus.yaml
    facia.yaml
    timpos.yaml

  handoffs/
    source_to_catalog.yaml
    catalog_to_admission.yaml
    admission_to_registration.yaml
    coordination_to_surface.yaml
    action_to_registration.yaml

  examples/
  tests/golden/

delivery/
  claude/
  chatgpt/
  codex/
```

## Keeper

```text
Roles do the work.
Protocol owns the rules.
YAML constrains the output.
Gestalt guards the handoff.
Timpos registers the change.
```
