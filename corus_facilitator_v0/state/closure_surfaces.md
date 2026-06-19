# Corus ClosureSurfaces State

This file preserves known places where WorkItems can close.

## Schema

```yaml
closure_surfaces:
  - id:
    type: async | one_on_one | meeting_with_people
    title:
    participants: []
    available_proof: []
    source_refs: []
    scheduled_at:
    labels: []
```

## Seed examples

```yaml
closure_surfaces:
  - id: surface.async_finance_followups
    type: async
    title: "Async finance/admin follow-ups"
    participants:
      - Jeremy
    available_proof: []
    source_refs:
      - src.h1_finance_admin_notes
    scheduled_at: null
    labels:
      - finance
      - admin

  - id: surface.h1_financial_review_session
    type: meeting_with_people
    title: "H1 financial review session"
    participants:
      - Jeremy
      - Members
      - Leadership
    available_proof:
      - ytd_revenue_snapshot
      - ytd_spending_snapshot
      - member_earnings_breakdown
      - aggregated_hour_estimates
    source_refs:
      - src.h1_finance_admin_notes
    scheduled_at: null
    labels:
      - finance
      - review

  - id: surface.h2_goal_review
    type: meeting_with_people
    title: "H2 goal review"
    participants:
      - Jeremy
      - Leadership
      - Members
    available_proof:
      - publishing_goal_status_snapshot
      - current_project_pipeline
    source_refs:
      - src.h1_finance_admin_notes
    scheduled_at: null
    labels:
      - goals
      - planning
```
