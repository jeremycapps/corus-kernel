# Corus Kernel v0

Corus Kernel derives context from minimal declared objects. Sources enter as raw documents; interpretation produces reviewable candidates; admitted artifacts and contracts feed boundary selection; moments record occurrence; context is derived deterministically.

## Model

```
source → interpret → artifact/contract → boundary → context
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
Timpos remembers occurrences.
Corus coordinates derived work state.
Fasia contextualizes that state into usable surfaces.
```

The active facilitator surface now lives under Fasia:

```text
fasia/facilitator/
├── protocol/
└── delivery/
    └── claude/
```

Keeper:

```text
Facilitator is the Fasia surface.
Protocol is the agent-agnostic format.
Claude is one delivery implementation.
```

See [Fasia Facilitator](docs/fasia_facilitator.md).

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
- [Fasia Facilitator](docs/fasia_facilitator.md) — facilitator as the first concrete candidate Fasia surface
- [Neara RVO fixture](docs/neara_rvo_fixture.md) — fixture walkthrough
- [ROADMAP.md](ROADMAP.md) — post-v0 items (commits, resolution_state, focus, surfaces)

## Fasia surfaces

- `fasia/facilitator/protocol/` — agent-agnostic facilitator protocol: prompt, schema, guardrails, examples, golden boundary cases
- `fasia/facilitator/delivery/claude/` — Claude-specific delivery package for the facilitator surface

## Archived discovery scaffolds

- `corus_facilitator_v0/` — markdown-first discovery scaffold, migrated to `fasia/facilitator/delivery/claude/`
- `corus_facilitator_v0_1/` — YAML-first discovery scaffold, migrated to `fasia/facilitator/protocol/`

## Tests

```bash
pip install pyyaml pytest
PYTHONPATH=. python -m pytest tests/ -v
```

Golden derive output: `tests/fixtures/neara_rvo_boundary_v0/golden/derive.json`
