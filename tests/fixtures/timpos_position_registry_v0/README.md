# Timpos Position Registry v0 Fixture

This fixture is intentionally scaffold-only. It is not yet loaded by `corus_kernel derive`.

It demonstrates the emerging Timpos primitive split:

```text
position_registry -> defines how source coordinate types resolve
positions         -> instantiate concrete source coordinates
timpos            -> timestamp positions
moments           -> record workstream-path values observed at timpos
```

## Files

```text
position_registry.yaml
positions.yaml
timpos.yaml
moments.yaml
```

## Object flow

```text
position_type: notion.page_property
  defines how to resolve a Notion page property

position: pos.hero_status
  points to the Status property on the Update Hero Layout page

timpo: timpo.001
  says pos.hero_status was observed at 2026-06-24T15:42:00-04:00

moment: moment.001
  says workstream.client_homepage_update/tasks/update-hero-layout/status = in_progress at timpo.001
```

## Why this matters

This makes Timpos feel Git-like:

```text
Workstream = repo
Path       = file path
Value      = file content/state
Moment     = commit-like path-value record
Previous   = parent pointer
Timpo      = when + where
Position   = where, by id
```

## Boundary from current Corus v0

Current Corus v0 moments are still occurrence moments:

```text
id + timpo + actor + via + object + previous
```

This fixture explores the lower Timpos-native path-value moment:

```text
id + workstream + path + value + timpo + previous
```

Do not replace the current derive fixture until the kernel schema has an explicit migration path.

## Next implementation steps

1. Add `position_types` and `positions` to `corus_kernel/schemas.py`.
2. Add `position_registry.yaml` and `positions.yaml` loading to `corus_kernel/loader.py`.
3. Add reference validation:
   - `position.type` must reference a registry type.
   - `timpo.p` must reference a position id.
4. Add a versioned moment schema or a distinct `path_moment` object.
5. Add replay/diff helpers for `workstream + path + value + previous`.

## Keeper

```text
Resolver registry tells you how to look.
Position tells you where to look.
Timpo tells you when you looked.
Moment tells you what changed.
```
