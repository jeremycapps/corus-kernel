# Timpos / Corus / Surface Boundary

## 1. Conceptual Separation

Timpos preserves observed state over time.

Corus derives coordination flow from current artifact state.

Surfaces render role-specific meaning.

The keeper:

```text
Moments preserve history.
Heads expose state.
Reducers derive work.
Surfaces render meaning.
```

Timpos is the primitive replay layer. It records observations and exposes the current state of opaque objects. It does not know what those objects mean.

Corus is the coordination layer. It consumes current artifact status, validates declared coordination objects, and derives readiness, output state, objective satisfaction, and next work.

The surface layer is the product layer. It turns replay and reducer output into role-specific meaning, demo narrative, evidence views, and human-facing interaction.

## 2. Near-Term Module Boundary

The repository stays together for now, but module ownership is hard:

```text
timpos/
  primitive replay objects

corus_v1/
  deterministic coordination reducer

demo/
  product rendering, claims, evidence, and workflow replay
```

Allowed dependency direction:

```text
demo -> corus_v1
demo -> timpos
corus_v1 -> timpos only through adapter-shaped data
timpos -> standard library only
```

Forbidden direction:

```text
timpos -> corus_v1
timpos -> demo
corus_v1 -> demo
```

## 3. Eventual Repo Split Criteria

Split repositories only when all are true:

```text
1. timpos has stable primitive replay APIs.
2. corus_v1 consumes replayed state only through an adapter boundary.
3. demo/product code can be removed without changing timpos or corus_v1 tests.
4. dependency tests prove no reverse imports.
5. release/version ownership differs across the layers.
```

Until then, an in-repo package boundary gives faster iteration with explicit constraints.

## 4. Interface Between Replay And Coordination

The stable interface is intentionally boring:

```python
replay_to_current_state(moment_log) -> object_state_map
object_state_map -> artifact_status_map
artifact_status_map + objective + contracts + artifacts -> flow
```

Timpos output:

```python
object_state_map = {
    "artifact.objective_spec": "validated",
    "artifact.architecture_spec": "present",
}
```

Corus adapter output:

```python
artifact_status_map = {
    "artifact.objective_spec": "validated",
    "artifact.architecture_spec": "present",
}
```

Only the Corus-side adapter decides that an opaque object id is an artifact status.

## 5. Constraints That Prevent Kernel Bloat

Timpos constraints:

```text
only object ids and observed states
no coordination object model
no product concepts
no interpretation
no dependency on corus_v1 or demo
```

Corus constraints:

```text
artifact status is consumed as current state
derived flow is not source state
contracts connect agents to artifacts
artifacts connect outputs to outputs
reducers derive who can act next
no product rendering
no demo-specific vocabulary
```

Surface constraints:

```text
may use replay output
may use Corus flow
may use claims, evidence, and product narrative
must not change Corus reducer semantics
must not introduce Timpos primitives
agentic interpretation belongs here
```

Future source, claim, evidence, and surface work must stay out of `corus_v1`.
Those concepts belong in the demo/product layer unless a future architecture
decision explicitly changes the boundary.

## 6. Migration Plan

```text
1. Keep corus_v1 reducer behavior stable.
2. Add timpos primitives as a separate package.
3. Add Corus replay adapter for object_state_map -> artifact_status_map.
4. Add tests for primitive replay determinism and dependency direction.
5. Keep demo/product concepts under demo/.
6. Move demo material into demo/neara/ only once the UI/product surface stabilizes.
7. Revisit repo split once APIs and ownership stabilize.
```

## 7. Test Plan

Tests should prove:

```text
timpos ids are deterministic
timpos replay produces object_state_map
object heads expose current state
timpos has no corus_v1 or demo imports
corus_v1 has no demo imports
corus_v1 still derives from declared artifact statuses without timpos
corus_v1 can consume replay output through replay_adapter
demo can use both timpos and corus_v1 without changing reducer output
```

## 8. Keeper

```text
Timpos preserves observed state over time.
Corus derives coordination flow from current artifact state.
Surfaces render role-specific meaning.

Moments preserve history.
Heads expose state.
Reducers derive work.
Surfaces render meaning.
```
