# Skill: Closure requirements

## Core idea

A WorkItem closes when its closure requirements are satisfied.

```text
closed = proof_satisfied AND authority_satisfied
```

Proof is evidence.
Authority is who can decide.

## Operators

Use only:

```text
any
all
none
```

Do not invent arbitrary functions in v0.

## Proof

Proof means evidence that can resolve a factual question.

Examples:

- invoice record
- payment receipt
- bank transaction
- signed document
- written confirmation
- submitted review
- shared link
- approved file

Proof examples:

```yaml
proof:
  any:
    - invoice_record
    - payment_receipt
    - bank_transaction
```

```yaml
proof:
  all:
    - updated_banking_document_received
    - filing_completed
```

## Authority

Authority means the named person or role required to decide.

Examples:

- Jeremy
- Leadership
- FinanceLead
- ClientOwner
- ProjectLead

Authority examples:

```yaml
authority:
  any:
    - Jeremy
    - FinanceLead
```

```yaml
authority:
  all:
    - Jeremy
    - Leadership
```

## None

Use `none: true` when a side is not required.

Example proof-only WorkItem:

```yaml
closure_requirements:
  proof:
    any:
      - invoice_record
      - payment_receipt
  authority:
    none: true
```

Example authority-only WorkItem:

```yaml
closure_requirements:
  proof:
    none: true
  authority:
    all:
      - Jeremy
      - Leadership
```

## Rules

- Do not mark authority required just because a person is attached.
- Do not mark proof required when the WorkItem is purely a choice.
- Some WorkItems need both proof and authority.
- Claude may propose requirements, but Corus must preserve them explicitly.
- Do not let closure requirements become a broad policy engine in v0.

## Keeper

Do not let Claude invent closure. Let Claude propose requirements; Corus stores and evaluates them.
