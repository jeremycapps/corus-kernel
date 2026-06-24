# Corus Kernel v0

Corus Kernel derives context from minimal declared objects. Sources enter as raw documents; interpretation produces reviewable candidates; admitted artifacts and contracts feed context coordination; moments record occurrence; context is derived deterministically.

## Model

```
source → interpret → artifact/contract → context
```

## Translation grammar

Corus uses two translation paths from an origin:

```
origin → how → what
origin → why → whom
```

An **origin** may be a person, event, or outcome.

The first path translates an origin into work:

```
origin → how → what
```

It asks how an origin becomes a concrete action, artifact, state, or decision.

The second path translates an origin into meaning:

```
origin → why → whom
```

It asks why an origin matters and which role, stakeholder, accountable party, or consumer it matters to.

In short:

```
origin → how → what   = execution path
origin → why → whom   = meaning path
```

## Layers

```text
Libera proposes.
Corus coordinates.
Facia prioritizes.
Timpos remembers.
```

Libera is the intake and proposal layer. It owns what was previously called the facilitator protocol.

```text
libera/
├── protocol/
└── delivery/
    └── claude/
```

Facia is the surface and priority layer.

```text
facia/
```

Keeper:

```text
Libera proposes candidate context from source material.
Corus coordinates admitted context state.
Facia renders surfaces, priorities, why, claims, and next actions.
Timpos records occurrences and state transitions.
```

See [Libera](docs/libera.md) and [Facia](docs/facia.md).

## Objects

**Declared objects** are authored YAML: `source`, `artifact`, `contract`, `role`, `team`, `profile`, `boundary`, `moment`, `timpo`.

**Derived objects** are computed by `derive`: `role_view`, `team_view`, `artifact_status`, `contract_status`, `context`, `context_state`, `trace`, `surface` (roadmap).

## Commands

```bash
# Interpret sources via fixture interpret_fixture.py → candidates (gitignored)
python -m corus_kernel interpret tests/fixtures/neara_rvo_boundary_v0

# Derive context from admitted declared objects
python -m corus_kernel derive tests/fixtures/neara_rvo_boundary_v0

# Select boundary when multiple exist
python -m corus_kernel derive tests/fixtures/neara_rvo_boundary_v0 --boundary boundary.neara.rvo.account_context
```

`derive` reads only admitted files (`artifacts.yaml`, `contracts.yaml`, etc.). It never reads `*.candidate.yaml`. Answer and trace claims are generated from derived context, not hard-coded fixture strings.

## Fixture

The Neara RVO boundary fixture lives at `tests/fixtures/neara_rvo_boundary_v0/`. See [docs/neara_rvo_fixture.md](docs/neara_rvo_fixture.md).

## Documentation

- [Architecture](docs/architecture.md) — declared vs derived, source roles, interpretation, context derivation
- [Libera](docs/libera.md) — intake and proposal layer, formerly facilitator
- [Facia](docs/facia.md) — surfaces, priorities, why, claims, and next actions
- [Neara RVO fixture](docs/neara_rvo_fixture.md) — fixture walkthrough
- [ROADMAP.md](ROADMAP.md) — post-v0 items (commits, resolution_state, focus, surfaces)

## Libera protocol

- `libera/protocol/` — agent-agnostic Libera protocol: prompt, schema, guardrails, examples, golden boundary cases
- `libera/delivery/claude/` — Claude-specific delivery package for Libera

## Archived discovery scaffolds

- `corus_facilitator_v0/` — archived markdown-first discovery scaffold, pre-Libera naming
- `corus_facilitator_v0_1/` — archived YAML-first discovery scaffold, pre-Libera naming

## Tests

```bash
pip install pyyaml pytest
PYTHONPATH=. python -m pytest tests/ -v
```

Golden derive output: `tests/fixtures/neara_rvo_boundary_v0/golden/derive.json`
