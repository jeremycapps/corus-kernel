# Corus WorkItems State

This file preserves unresolved work that Corus can test for closure.

## Schema

```yaml
work_items:
  - id:
    title:
    question:
    status: open | closed
    closure_requirements:
      proof:
        any: []
        all: []
        none: true | false
      authority:
        any: []
        all: []
        none: true | false
    attached_people: []
    suggested_surface_type: async | one_on_one | meeting_with_people
    source_refs: []
    first_seen:
    last_seen:
    notes:
```

## Seed WorkItems from H1 finance/admin notes

```yaml
work_items:
  - id: work.tiffany_banking_document
    title: "Tiffany banking document"
    question: "Has Tiffany sent the updated banking document so the filing can be completed?"
    status: open
    closure_requirements:
      proof:
        all:
          - updated_banking_document_received
          - filing_completed
      authority:
        none: true
    attached_people:
      - Tiffany
      - Jeremy
    suggested_surface_type: async
    source_refs:
      - src.h1_finance_admin_notes
    first_seen: 2026-06-18
    last_seen: 2026-06-18
    notes: "Banking/account setup is waiting on Tiffany's updated document."

  - id: work.terrell_outstanding_invoice
    title: "Terrell outstanding invoice"
    question: "Has Terrell's outstanding invoice been confirmed and paid?"
    status: open
    closure_requirements:
      proof:
        all:
          - terrell_invoice_confirmed
          - payment_record
      authority:
        none: true
    attached_people:
      - Terrell
      - Jeremy
    suggested_surface_type: async
    source_refs:
      - src.h1_finance_admin_notes
    first_seen: 2026-06-18
    last_seen: 2026-06-18
    notes: "Invoice flagged as needing follow-up."

  - id: work.ivy_second_invoice
    title: "Ivy second outstanding invoice"
    question: "Has Ivy's second outstanding invoice been located and paid?"
    status: open
    closure_requirements:
      proof:
        all:
          - ivy_second_invoice_located
          - payment_record
      authority:
        none: true
    attached_people:
      - Ivy
      - Jeremy
    suggested_surface_type: async
    source_refs:
      - src.h1_finance_admin_notes
    first_seen: 2026-06-18
    last_seen: 2026-06-18
    notes: "First Ivy invoice of $2,500 was paid May 1st. This WorkItem concerns the second invoice only."

  - id: work.ytd_financial_review
    title: "YTD financial review"
    question: "Has Jeremy prepared the YTD financial review covering revenue, spending, member earnings, and aggregated hour estimates?"
    status: open
    closure_requirements:
      proof:
        all:
          - ytd_revenue_snapshot
          - ytd_spending_snapshot
          - member_earnings_breakdown
          - aggregated_hour_estimates
      authority:
        none: true
    attached_people:
      - Jeremy
    suggested_surface_type: async
    source_refs:
      - src.h1_finance_admin_notes
    first_seen: 2026-06-18
    last_seen: 2026-06-18
    notes: "Hours can be ballpark estimates. Review should support individual reviews and H2 goal-setting."

  - id: work.h2_publishing_goal_decisions
    title: "H2 publishing goal decisions"
    question: "Which H2 publishing goals remain active, revised, or at risk?"
    status: open
    closure_requirements:
      proof:
        any:
          - publishing_goal_status_snapshot
          - current_project_pipeline
      authority:
        all:
          - Jeremy
          - Leadership
    attached_people:
      - Jeremy
      - Leadership
      - Publishing
    suggested_surface_type: meeting_with_people
    source_refs:
      - src.h1_finance_admin_notes
    first_seen: 2026-06-18
    last_seen: 2026-06-18
    notes: "Goals include $10K publishing revenue, 3 books published, 50 paid subscribers, and 50 stories published."
```
