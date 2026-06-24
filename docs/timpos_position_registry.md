# Timpos Position Registry

## Keeper

```text
Resolver registry tells you how to look.
Position tells you where to look.
Timpo tells you when you looked.
Moment tells you what changed.
```

This document scaffolds the next Timpos primitive split inside Corus Kernel.

The current kernel already treats `timpo` as the time-position address of an occurrence and `moment` as the minimal occurrence atom. The next refinement is to make `timpo.p` reference a declared `position` instead of carrying a raw logical placeholder.

## Current kernel fit

Current declared objects include:

```text
source
artifact
contract
role
team
profile
boundary
moment
timpo
```

The current architecture says:

```text
Moment = timpo + actor + via + object + previous
Timpo = t + p
```

The proposed Timpos split keeps that shape but makes `p` more precise:

```text
position_type  -> reusable resolver definition
position       -> concrete source coordinate
timpo          -> time + position_id
moment         -> workstream/path/value + timpo + previous
```

## Why this belongs below Corus

Timpos should not know whether a source is valuable, admitted, blocked, customer-facing, or review-ready.

Timpos should only preserve:

```text
what value was observed
where it was observed
when it was observed
what previous observation it follows
```

Corus can then derive coordination from those path/value changes.

## Object responsibilities

### Position type

A `position_type` is a reusable resolver contract.

It defines:

```text
what locator fields are required
how to build a canonical URI
which resolver protocols may retrieve it
```

Example:

```yaml
position_type:
  id: notion.page_property
  locator_schema:
    workspace_id: string
    page_id: string
    property_name: string
  canonical_uri_template: "notion://workspace/{workspace_id}/page/{page_id}#property={property_name}"
```

### Position

A `position` is one concrete source coordinate.

Example:

```yaml
position:
  id: pos.hero_status
  type: notion.page_property
  locator:
    workspace_id: acme
    page_id: page_update_hero_layout
    property_name: Status
```

The same position can be observed many times.

### Timpo

A `timpo` binds time to a position.

Example:

```yaml
timpo:
  id: timpo.001
  t: 2026-06-24T15:42:00-04:00
  p: pos.hero_status
```

Timpo does not store connector details. It only stores time and position id.

### Moment

A `moment` records a workstream-path value observed at a Timpo.

Proposed Timpos-native moment shape:

```yaml
moment:
  id: moment.001
  workstream: workstream.client_homepage_update
  path: tasks/update-hero-layout/status
  value: ready_for_client_review
  timpo: timpo.001
  previous: moment.000
```

This differs from the current Corus v0 `moment` shape, which records contextual occurrence through `actor`, `via`, and `object`.

That means this should land as a Timpos primitive refinement before replacing current Corus moments.

## Current Corus v0 vs Timpos primitive refinement

| Concern | Current Corus v0 moment | Timpos primitive moment |
|---|---|---|
| Purpose | Records contextual occurrence for derivation | Records state value at workstream path |
| Shape | `id`, `timpo`, `actor`, `via`, `object`, `previous` | `id`, `workstream`, `path`, `value`, `timpo`, `previous` |
| Meaning | Corus-aware | Corus-neutral |
| Best use | Current Neara boundary derivation | Git-like Timpos replay/diff |

## Recommended migration path

### Phase 0 — Scaffold only

Add docs and fixtures:

```text
docs/timpos_position_registry.md
tests/fixtures/timpos_position_registry_v0/
  position_registry.yaml
  positions.yaml
  timpos.yaml
  moments.yaml
  README.md
```

Do not change the existing strict schema yet.

### Phase 1 — Add declared position objects

Add new declared collections:

```text
position_types
positions
```

Update:

```text
corus_kernel/schemas.py
corus_kernel/loader.py
corus_kernel/validate.py
```

Validation rules:

```text
timpo.p must reference a position.id
position.type must reference a position_type.id
position.locator must satisfy the position_type.locator_schema
```

### Phase 2 — Introduce Timpos-native moments

Add a second moment family or versioned moment schema:

```text
moment.v0.corus_occurrence
moment.v1.timpos_path_value
```

Do not silently overload the existing `moment` object.

### Phase 3 — Add replay/diff

Build Timpos replay around:

```text
workstream + path + value + previous
```

Corus derives coordination from replayed heads.

## Non-goals

Do not put these into Timpos:

```text
MCP auth
API credentials
retrieval results
surface rendering
admission decisions
claim status
role-specific meaning
```

Those belong above or beside Timpos.

## Final keeper

```text
Position is the source coordinate.
Timpo binds that coordinate to time.
Moment binds that timed coordinate to a workstream path value.
Corus derives coordination from the resulting diffs.
```
