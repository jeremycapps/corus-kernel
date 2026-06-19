# Example: H1 review, finance, admin, and H2 goals

This example uses meeting notes to produce Corus WorkItems.

## Source summary

The meeting included:

- banking follow-up with Tiffany
- Terrell and Ivy invoice follow-ups
- YTD financial review preparation
- internal hours estimate gap
- individual H1 review workflow
- H2 goal review
- NDFJA payout planning

## Extracted WorkItems

```yaml
work_items:
  - id: work.tiffany_banking_document
    title: "Tiffany banking document"
    question: "Has Tiffany sent the updated banking document so the filing can be completed?"
    closure_requirements:
      proof:
        all:
          - updated_banking_document_received
          - filing_completed
      authority:
        none: true
    suggested_surface_type: async

  - id: work.ivy_second_invoice
    title: "Ivy second outstanding invoice"
    question: "Has Ivy's second outstanding invoice been located and paid?"
    closure_requirements:
      proof:
        all:
          - ivy_second_invoice_located
          - payment_record
      authority:
        none: true
    suggested_surface_type: async

  - id: work.h2_publishing_goal_decisions
    title: "H2 publishing goal decisions"
    question: "Which H2 publishing goals remain active, revised, or at risk?"
    closure_requirements:
      proof:
        any:
          - publishing_goal_status_snapshot
          - current_project_pipeline
      authority:
        all:
          - Jeremy
          - Leadership
    suggested_surface_type: meeting_with_people
```

## Facilitation read

Async can close proof-only items such as banking docs and invoice confirmation.

A meeting with people is required for H2 publishing goal decisions because the WorkItem needs both a status snapshot and authority from Jeremy plus Leadership.

## Keeper

No closure requirement, no meeting agenda item.
