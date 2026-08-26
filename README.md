# Corus Kernel

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

## Packages

The repository holds four packages with hard module ownership:

```text
timpos/        primitive replay objects (standard library only)
corus_kernel/  declared-object kernel v0: interpret, validate, derive
corus_v1/      deterministic coordination reducer over a .corus/ bundle
fasia/         relations, translation, and packets
corus_agents/  runtime workers that operate the kernel pipeline
demo/          product rendering, claims, evidence, workflow replay
```

Allowed dependency direction:

```text
demo -> corus_v1, timpos, fasia
fasia -> nothing in this repo
corus_v1 -> timpos only through replay_adapter
timpos -> standard library only
```

`fasia` imports neither `corus_v1` nor `timpos`. It receives derived flow, node
states, and artifact statuses as explicit arguments, and dependency tests
enforce this. See [the boundary doc](docs/architecture/timpos_corus_boundary.md).

### Timpos — memory

Primitive replay. Timpos records observations of opaque objects and exposes
their current state. It does not know what those objects mean.

```text
Position  opaque location string
Timpo     id + t + p, the time-position address of an occurrence
Moment    timpo + object + state + previous
ObjectHead  object + moment + state
```

```python
from timpos import Moment, Timpo, replay_to_current_state

timpo = Timpo.create(t="1", p="self_build")
moment = Moment.create(timpo=timpo, object="artifact.objective_spec", state="validated")
replay_to_current_state([moment])
# {"artifact.objective_spec": "validated"}
```

Ids are deterministic sha256 prefixes over canonical JSON, so replay is
reproducible.

### Corus — coordination

Two coordination surfaces live side by side.

`corus_kernel` is the declared-object kernel v0. **Declared objects** are
authored YAML: `source`, `artifact`, `contract`, `role`, `team`, `profile`,
`boundary`, `moment`, `timpo`. **Derived objects** are computed by `derive`:
`role_view`, `team_view`, `artifact_status`, `contract_status`, `context`,
`context_state`, `trace`.

`corus_v1` is the deterministic reducer used by the self-build and demo work.
It loads a project bundle from `.corus/` (`project`, `agents`, `objectives`,
`artifacts`, `contracts`) and derives readiness, output state, objective
satisfaction, and next work. It consumes replayed Timpos state only through
`corus_v1/replay_adapter.py`, which is what decides an opaque object id is an
artifact status.

The two use different moment shapes on purpose:

```text
corus_kernel  Moment = timpo + actor + via + object + previous
timpos        Moment = timpo + object + state + previous
```

`corus_kernel` records who acted and through what; `timpos` records only
observed state. They are not interchangeable.

### Fasia — relation

Relation existence is authored. Path state is derived. Translation is what
Fasia does over relations.

```text
Relation = id + initiator + target + sources[] + objectives[]
Target   = type (object | subject) + id + label
DerivedRelation = relation + path + label + reasons[]
```

A path is `open` or `closed`, and the derived label follows from target type
and path:

```text
object  + open   -> enables
object  + closed -> blocks
subject + open   -> affects
subject + closed -> risks
```

A path closes for one or more explicit reasons: `source_not_admitted`,
`objective_out_of_scope`, `initiator_unusable`, `target_unusable`,
`target_blocked_by_corus_readiness`.

```python
from fasia import Relation, Target, derive_relation_paths

relation = Relation(
    id="relation.rvo_output.integration_path",
    initiator="artifact.rvo_output",
    target=Target(
        type="object",
        id="artifact.integration_path",
        label="Integration path",
    ),
    sources=("source.neara_rvo_context",),
    objectives=("objective.customer_system_mapping",),
)

derive_relation_paths(
    [relation],
    admitted_sources=["source.neara_rvo_context"],
    active_objectives=["objective.customer_system_mapping"],
    node_states={"artifact.integration_path": "expected_missing"},
)
# [{"relation": "relation.rvo_output.integration_path",
#   "path": "closed", "label": "blocks", "reasons": ["target_unusable"]}]
```

**Translation modes v0.** Relation declares a contextual edge, path says
whether it can currently count, and translation mode says what movement of
context the edge supports:

```text
consumer -> discovery -> objective
objective -> strategy -> value
value    -> product   -> consumer
```

`translate_relations(relations, mode, ...)` returns one translation edge over
derived paths. `classify_translation_mode(relation)` infers the mode from node
id prefixes (`consumer.*`, `objective.*`, `value.*`) and returns `None` when
the movement is not one of the three. Fasia v0 does not add a `Relation.mode`
field.

**Packets** are Fasia's structured output over Corus flow, one per Corus
relation:

```text
objective scope   -> derive_objective_packet   goal state
contract.executor -> derive_implement_packet   what can be produced
contract.consumer -> derive_validate_packet    what can be accepted or rejected
```

Packets are structured data, not prose. They do not mutate the flow they read.
Fasia is deterministic, calls no LLMs, renders no UI, and encodes no job
titles.

### Agents

`corus_agents/` are runtime workers over the kernel pipeline: source inventory,
preprocessing, interpretation, admission, derive, and the plain English
readout. Agents may not introduce kernel objects — `commit`, `resolution_state`,
`rule`, `state_rule`, and `"surface"` keys are rejected by
`tests/test_agents_audit.py`.

### Demo

`demo/` owns product concepts — source refs, claims, evidence, and the RVO
workflow replay page. Source, claim, evidence, and Fasia packet work belongs
outside `corus_v1`. Keep it in Fasia, demo, or product layers until there is a
deliberate boundary change.

## Commands

Kernel v0:

```bash
# Interpret sources via fixture interpret_fixture.py → candidates (gitignored)
python -m corus_kernel interpret tests/fixtures/neara_rvo_boundary_v0

# Derive context from admitted declared objects
python -m corus_kernel derive tests/fixtures/neara_rvo_boundary_v0

# Select boundary when multiple exist
python -m corus_kernel derive tests/fixtures/neara_rvo_boundary_v0 --boundary boundary.neara.rvo.account_context
```

`derive` reads only admitted files (`artifacts.yaml`, `contracts.yaml`, etc.). It never reads `*.candidate.yaml`. Answer and trace claims are generated from derived context, not hard-coded fixture strings.

Coordination reducer, over `.corus/` at the repo root by default:

```bash
# Derive self-build coordination state as JSON
python -m corus_v1 derive

# Render derived contract states as text
python -m corus_v1 render

# Point at another bundle, or write to a file
python -m corus_v1 derive --project path/to/project -o derive.json
```

Agent pipeline:

```bash
# Run the full pipeline over a fixture
python -m corus_agents run tests/fixtures/neara_rvo_boundary_v0

# Admission report; add --approve to promote candidates after review
python -m corus_agents admit tests/fixtures/neara_rvo_boundary_v0
```

Demo replay:

```bash
# RVO context replay as text
python -m demo.rvo_replay

# ...as JSON, or as a static page
python -m demo.rvo_replay --json
python -m demo.rvo_replay --html demo/rvo_replay.html
```

`timpos` and `fasia` are libraries with no CLI. They are used through their
Python APIs, as above.

## Fixture

The Neara RVO boundary fixture lives at `tests/fixtures/neara_rvo_boundary_v0/`. See [docs/neara_rvo_fixture.md](docs/neara_rvo_fixture.md). The demo replay fixture lives at `demo/fixtures/rvo/`.

## Documentation

- [Architecture](docs/architecture.md) — declared vs derived, source roles, interpretation, context derivation (kernel v0)
- [Timpos / Corus / Fasia boundary](docs/architecture/timpos_corus_boundary.md) — layer separation, dependency rules, translation modes, packet boundary
- [Neara RVO fixture](docs/neara_rvo_fixture.md) — fixture walkthrough
- [Demo build control](docs/demo_build_control.md) — demo ownership and admission questions
- [ROADMAP.md](ROADMAP.md) — what is open, what shipped, and what is deliberately deferred

## Tests

```bash
pip install pyyaml pytest
PYTHONPATH=. python -m pytest tests/ -v
```

Dependency direction is enforced by tests, not convention:
`tests/test_layer_boundaries.py`, `tests/test_corus_v1_boundary.py`, and the
boundary tests at the end of `tests/test_fasia.py` and
`tests/test_timpos_primitives.py`.

Golden derive output: `tests/fixtures/neara_rvo_boundary_v0/golden/derive.json`
