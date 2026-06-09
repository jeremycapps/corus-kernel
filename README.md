# Corus Kernel v0

Corus Kernel derives context from minimal declared objects. Sources enter as raw documents; interpretation produces reviewable candidates; admitted artifacts and contracts feed boundary selection; moments record occurrence; context is derived deterministically.

## Model

```
source → interpret → artifact/contract → boundary → context
```

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
- [Neara RVO fixture](docs/neara_rvo_fixture.md) — fixture walkthrough
- [ROADMAP.md](ROADMAP.md) — post-v0 items (commits, resolution_state, focus, surfaces)

## Tests

```bash
pip install pyyaml pytest
PYTHONPATH=. python -m pytest tests/ -v
```

Golden derive output: `tests/fixtures/neara_rvo_boundary_v0/golden/derive.json`
