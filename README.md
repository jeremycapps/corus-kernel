# Corus

Corus is a YAML-first coordination protocol for replayed workstream state.

Libera defines where workstream state lands.
Timpos records observed changes.
Corus replays those changes into coordination state.
Fasia renders coordinated meaning.

## Keeper

```text
Libera defines the address.
Timpos records the change.
Corus derives coordination.
Fasia renders meaning.
```

## Core model

```text
libera workflow + timpos moments + corus reducers
→ coordination_state
```

## What Corus answers

```text
What exists?
What is missing?
What is blocked?
What is ready?
What changed?
What should happen next?
Which role needs attention?
```

## Core files

```text
protocol/
  README.md
  objective.schema.yaml
  contract.schema.yaml
  reducer.schema.yaml
  coordination_state.schema.yaml
  next_action.schema.yaml

docs/
  timpos_libera_boundary.md
  reducer_model.md

examples/
  client_homepage_update/
    corus.yaml
    expected_coordination_state.yaml

  design_systems_bug/
    libera.yaml
    timpos.yaml
    moments.yaml
    corus.yaml
    expected_coordination_state.yaml
```

## What Corus is not

Corus does not define source locators.
Corus does not record observations.
Corus does not own workstream path grammar.
Corus does not render final product surfaces.
Corus does not replace Timpos or Libera.

## Layer boundary

```text
Libera:
  Defines valid workstream paths and local values.

Timpos:
  Records path changes at source-located times.

Corus:
  Replays those changes and derives coordination state.

Fasia:
  Turns coordination state into faces and surfaces.
```

## Status

Corus v1 is YAML-first. No runtime code is included in this scaffold.
