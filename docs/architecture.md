# Corus Kernel Architecture

## Keeper

Sources enter.
Artifacts have origin, subject, and status.
Contracts assign artifacts to roles.
Boundaries select contracts by team plus subject.
Moments record contextual occurrence.
Context is derived.

## Declared vs derived

| Declared | Derived |
|----------|---------|
| `source` | `role_view` |
| `artifact` | `team_view` |
| `contract` | `artifact_status` |
| `role` | `contract_status` |
| `team` | `context` |
| `profile` | `context_state` |
| `boundary` | `trace` |
| `moment` | `surface` (roadmap) |
| `timpo` | |

Declared objects are minimal YAML records with only allowed fields. Extra fields fail validation.

Derived objects are never authored directly. They are produced by `derive` from declared objects plus fixed reducer rules.

## Source roles: subject vs origin

The same `source` type plays different relationship roles:

- **Subject** — intelligence the team coordinates around. RVO (`source.neara_rvo`) is the boundary subject. It is not the origin of CVA/FDE artifacts.
- **Origin** — where artifact interpretation comes from. CVA and FDE job descriptions are origins for value and technical artifacts respectively.
- **Orchestrator basis** — Director JD justifies the boundary orchestrator profile; it does not produce v0 artifacts.
- **Loaded but excluded** — Data Scientist source is available for future roles but excluded from v0 because its role is not on the team.

RVO is never `artifact.origin` for CVA/FDE artifacts. CVA/FDE job descriptions are never `boundary.subject`.

## Why interpretation is explicit

Source PDFs do not silently become artifacts. The `interpret` command reads `sources/sources.yaml` and optionally runs a fixture-local `interpret_fixture.py` module (test machinery, not a declared object), then writes:

- `artifacts.candidate.yaml`
- `contracts.candidate.yaml`
- `interpretation_trace.json`

These files are gitignored. After human review, candidates are copied to admitted `artifacts.yaml` and `contracts.yaml`. This keeps provenance traceable: every artifact has a declared origin and subject.

## Role, team, profile separation

- **Role** groups contracts (`contract.owner`).
- **Team** groups roles (`team.roles`). Boundary selection uses team membership.
- **Profile** acts in moments (`moment.actor`). The boundary orchestrator is a profile reference.

## Boundary selection

A boundary contains only: `id`, `label`, `orchestrator`, `team`, `subject`.

Contracts are selected when:

```
contract.owner in boundary.team.roles
and contract.artifact.subject == boundary.subject
```

## Context derivation

`derive` loads admitted declared objects, validates minimalism and references, selects contracts and artifacts through the boundary, attaches relevant moments, and reduces `context_state`:

| Condition | coordination | reason |
|-----------|--------------|--------|
| missing subject | `blocked` | `missing_subject` |
| any artifact `expected_missing` or `rejected` | `unresolved` | `missing_or_rejected_artifacts` |
| all artifacts `present` or `validated` | `ready` | `selected_artifacts_satisfied` |

Output includes deterministic hashes and trace claims.

## Moment atom

A moment contains only: `id`, `timpo`, `actor`, `via`, `object`, `previous`.

```
Moment = timpo + actor + via + object + previous
```

Timpo (`t`, `p`) is the time-position address of an occurrence — not `created_at`.

## Roadmap (not in v0)

These are intentionally absent from v0:

- **Commit** — artifact commit history
- **resolution_state** — named outcomes beyond default coordination
- **focus/purpose enum** — purpose-driven selection
- **state_rule** — custom reducers
- **Timpo physical/executional encoding** — beyond logical integers
- **Data Scientist role extension** — model/data artifacts

Surface rendering has since shipped outside the kernel and the term was
retired: structured views are Fasia packets, and the plain English readout is
`corus_agents/surface_agent.py`. `"surface"` remains forbidden as a kernel
object key.

See [ROADMAP.md](../ROADMAP.md).
