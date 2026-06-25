# Corus Reducer Model

Corus reducers are YAML-described deterministic derivation rules.

They read replayed workstream state and emit coordination state.

```text
replayed current state + contracts + reducers
→ coordination_state
```

## Reducer kinds

```text
missing_paths
blocker
readiness
next_action
role_attention
diff
```

## Rules

```text
Reducers derive.
Reducers do not record.
Reducers do not retrieve.
Reducers do not render final faces.
```

A reducer may reference Libera paths, Timpos moment ids, contract ids, and prior coordination state sections.

## Example

```yaml
reducers:
  - id: reducer.missing_required_paths
    type: missing_paths
    inputs:
      - contracts
      - current
    emits:
      - missing

  - id: reducer.next_action
    type: next_action
    inputs:
      - missing
      - blocked
      - role_attention
    emits:
      - next_actions
```
