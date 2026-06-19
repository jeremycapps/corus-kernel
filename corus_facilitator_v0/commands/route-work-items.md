# /corus:route-work-items

Use this command when there are multiple WorkItems and the user needs to know where each should close.

## Purpose

Route WorkItems to the right closure surface.

Closure surface types are intentionally limited:

```text
async
1:1
meeting_with_people
```

Everything else is a title or label, not a type.

## Inputs

- WorkItems.
- Known participants or required people.
- Available proof sources.
- Known meetings or async channels, when available.

## Routing rules

### async

Route to `async` when closure can happen through proof, written confirmation, or simple recorded approval.

Default signals:

- proof-only WorkItem
- no live discussion needed
- evidence can be sent, uploaded, or confirmed

### 1:1

Route to `1:1` when one named person’s context, judgment, clarification, or authority is required.

Default signals:

- one person can resolve ambiguity
- sensitive/person-specific context
- direct clarification needed

### meeting_with_people

Route to `meeting_with_people` when multiple people must align, decide, or provide context.

Default signals:

- authority requires more than one person or role
- tradeoff decision
- cross-person coordination
- shared review or steering discussion

## Output shape

```yaml
routed_work_items:
  async:
    - work_item_id:
      reason:
      required_proof: []
  one_on_one:
    - work_item_id:
      reason:
      required_person:
  meeting_with_people:
    - work_item_id:
      reason:
      required_people: []
      required_authority: []
  needs_more_context:
    - work_item_id:
      missing:
```

## Rules

- Prefer the smallest closure surface that can close the WorkItem.
- Do not route to a meeting with people when async is enough.
- Do not route to a group meeting when a 1:1 is enough.
- Do not route an item anywhere unless the closure requirement is named.

## Keeper

Corus routes WorkItems to the surface where they can actually close.
