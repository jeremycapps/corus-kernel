# Corus Kernel Roadmap

## Open beyond v0

1. **Artifact commit history** — track artifact evolution through explicit commits.
2. **Resolution state** — named outcomes beyond default coordination reducer.
3. **Focus/purpose enum** — purpose-driven contract and boundary selection.
4. **Boundary selection modes** — multiple boundaries, selection criteria, and priority.
5. **State rules** — custom reducers beyond the default coordination reducer.
6. **Timpo physical/executional encoding** — extend timpo beyond logical integers.

Items 1, 2, and 5 are actively held out of the kernel, not merely unbuilt.
`FORBIDDEN_KERNEL_OBJECTS` in `tests/test_agents_audit.py` fails the build if
`commit`, `resolution_state`, `rule`, or `state_rule` appear in agent code.
Adding any of them is a deliberate boundary change, not an increment.

Item 4 is partly scaffolded: `derive --boundary` selects among boundaries, but
the fixture declares only one and there are no selection criteria or priority
rules yet.

Item 6 has a reference implementation in the separate `corus-workbench` repo,
where `timpo/` encodes when + where as a `UInt128` of latitude/longitude
milli-arcseconds plus nanoseconds since epoch. Kernel timpos are still logical
(`t: 1, p: 1`), and `timpos.Timpo` takes `t` and `p` as opaque strings. Adopting
the physical encoding here means reconciling two different Timpo designs — the
workbench one has no separate Timpo id.

## Delivered since v0

- **Surface rendering** → shipped in two places, and the term was retired.
  `a57c773` renamed surfaces to Fasia context translation. Structured views are
  Fasia packets (`fasia/objective.py`, `implement.py`, `validate.py`); the plain
  English readout over derived context is `corus_agents/surface_agent.py`.
  `"surface"` is now forbidden as a kernel object key, enforced by
  `FORBIDDEN_SURFACE_OBJECT` in `tests/test_agents_audit.py`.
- **Relation layer** — `fasia/` derives open/closed path state over authored
  relations, with translation modes v0.
- **Primitive replay** — `timpos/` records observed object state and replays it
  to heads, with no dependency on coordination objects.
- **Coordination reducer** — `corus_v1/` derives readiness, output state,
  objective satisfaction, and next work from a `.corus/` bundle.

## Deliberately deferred

- **Data Scientist role extension** — the source is recognized, not extended.
  `corus_agents/bootstrap_interpreter.py` classifies it as
  `future_artifact_origin` with `admission_required: false` and the reason
  `role_not_on_v0_team`. Model and data artifacts follow only once the role
  joins a v0 team.
- **Source, claim, and evidence work** — stays out of `corus_v1`. It belongs in
  Fasia, demo, or product layers until a deliberate boundary change.

See [docs/architecture/timpos_corus_boundary.md](docs/architecture/timpos_corus_boundary.md) for the layer rules these items have to respect.
