# Corus Kernel v0

Corus Kernel derives context from minimal declared objects. Sources enter as raw documents; interpretation produces reviewable candidates; admitted artifacts and contracts feed boundary selection; moments record occurrence; context is derived deterministically.

## Model

```
source → interpret → artifact/contract → boundary → context
```

## Layer Boundary

```text
Timpos = memory
Corus = coordination
Fasia = relation
```

Timpos structures time through Moments. Corus structures obligation through Contracts. Fasia structures context through Relations.

The keeper:

```text
Moments make time addressable.
Contracts make obligation addressable.
Relations make context addressable.
```

Fasia primitive:

```text
Relation = id + initiator + target + sources[] + objectives[]
```

Relation existence is authored. Path state is derived. Translation is what Fasia does over relations.

Source, claim, evidence, and Fasia packet work belongs outside `corus_v1`. Keep it in Fasia, demo, or product layers until there is a deliberate boundary change.

**Declared objects** are authored YAML: `source`, `artifact`, `contract`, `role`, `team`, `profile`, `boundary`, `moment`, `timpo`.

**Derived objects** are computed by `derive`: `role_view`, `team_view`, `artifact_status`, `contract_status`, `context`, `context_state`, `trace`.

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
- [Timpos / Corus / Fasia boundary](docs/architecture/timpos_corus_boundary.md) — memory, coordination, and relation layers
- [Neara RVO fixture](docs/neara_rvo_fixture.md) — fixture walkthrough
- [ROADMAP.md](ROADMAP.md) — post-v0 items (commits, resolution_state, focus)

## Tests

```bash
pip install pyyaml pytest
PYTHONPATH=. python -m pytest tests/ -v
```

Golden derive output: `tests/fixtures/neara_rvo_boundary_v0/golden/derive.json`
