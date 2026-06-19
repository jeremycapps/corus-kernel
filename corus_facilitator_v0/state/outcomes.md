# Corus Outcomes State

This file records what happened to WorkItems after a closure attempt.

Allowed records use these result values:

- created
- closed
- blocked
- moved
- carried_over
- reopened

## Schema

```yaml
records:
  - id:
    work_item_id:
    surface_id:
    result:
    proof_accepted: []
    authority_accepted: []
    missing_proof: []
    missing_authority: []
    reason:
    next_surface_type:
    next_surface_id:
    timestamp:
```

## Current records

```yaml
records: []
```
