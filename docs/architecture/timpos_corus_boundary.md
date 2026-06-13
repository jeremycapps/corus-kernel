# Timpos / Corus / Fasia Boundary

## 1. Conceptual Separation

Timpos preserves observed state over time.

Corus derives coordination flow from current artifact state.

Fasia structures context through deterministic translation.

The keeper:

```text
Moments preserve history.
Heads expose state.
Reducers derive work.
Fasia translates context.
```

Current stack:

```text
Timpos remembers.
Corus coordinates.
Fasia translates.
Agents act.
Renderers display.
```

Timpos is the primitive replay layer. It records observations and exposes the current state of opaque objects. It does not know what those objects mean.

Corus is the coordination layer. It consumes current artifact status, validates declared coordination objects, and derives readiness, output state, objective satisfaction, and next work.

Fasia is the context-translation layer. Its primitive context is subject plus consumer, objective, value, and state. Its first structured packet outputs are Objective, Implement, and Validate packets over Corus flow.

## 2. Near-Term Module Boundary

The repository stays together for now, but module ownership is hard:

```text
timpos/
  primitive replay objects

corus_v1/
  deterministic coordination reducer

demo/
  product rendering, claims, evidence, and workflow replay

fasia/
  deterministic context translation and packets
```

Allowed dependency direction:

```text
demo -> corus_v1
demo -> timpos
demo -> fasia
fasia -> corus_v1
fasia -> timpos, only when replay trace is needed
corus_v1 -> timpos only through adapter-shaped data
timpos -> standard library only
```

Forbidden direction:

```text
timpos -> corus_v1
timpos -> demo
timpos -> fasia
corus_v1 -> demo
corus_v1 -> fasia
fasia -> demo
fasia -> UI components
fasia -> agent runtime behavior
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

Fasia constraints:

```text
deterministic for the same flow and inputs
structured as fields, queues, actions, refs, and trace IDs
relation-scoped over objective_scope, executor, or consumer
may use claims and evidence only if supplied by the product layer
must not change Corus reducer semantics
must not introduce Timpos primitives
must not call LLMs
must not render UI
must not encode job titles
```

Future source, claim, and evidence work must stay out of `corus_v1`.
Those concepts belong in the demo/product layer unless a future architecture
decision explicitly changes the boundary. Fasia packets belong in `fasia/`.

## 6. Fasia Boundary

Fasia structures context by translating between consumer, objective, and value.

The primitive context shape is:

```text
Context = subject + consumer + objective + value + state
```

Translation is the umbrella operation:

```text
Discovery: consumer -> objective
Strategy: objective -> value
Product: value -> consumer
```

Fasia packets are structured outputs. They are not the whole of Fasia.

A Fasia packet is not:

```text
a UI page
an API endpoint
an autonomous agent
an LLM summary
a product narrative
a demo-specific view
```

Initial packet mapping follows Corus relations:

```text
Objective scope   -> Objective packet
Contract.executor -> Implement packet
Contract.consumer -> Validate packet
```

Objective shows the state of the goal.

Implement shows what can be produced.

Validate shows what can be accepted or rejected.

Agents, commands, APIs, and renderers can consume Fasia packets. `corus_v1`
must not import `fasia`. `fasia` must not import demo or agent runtime
behavior.

Fasia invariants:

```text
1. Fasia is deterministic.
2. Fasia packets are structured data.
3. Fasia does not mutate Timpos or Corus state.
4. Fasia packets are not prose.
5. Fasia does not call LLMs.
6. Fasia does not encode UI labels, product labels, or job titles.
```

Dependency diagram:

```text
+------------------+
|     timpos       |
|------------------|
| Position         |
| Timpo            |
| Moment           |
| ObjectHead       |
| Replay           |
+---------+--------+
          |
          | replay_to_current_state()
          v
+--------------------------+
| object_state_map         |
+------------+-------------+
             |
             | adapter maps artifact.* objects
             v
+--------------------------+
| artifact_status_map      |
+------------+-------------+
             |
             v
+------------------+
|    corus_v1      |
|------------------|
| Objective        |
| Agent            |
| Contract         |
| Artifact         |
| Reducer          |
+---------+--------+
          |
          | derive()
          v
+------------------+
| flow / next work |
+---------+--------+
          |
          | context translation / packet projection
          v
+------------------+
|      fasia       |
|------------------|
| Context          |
| Translation      |
| Packets          |
+---------+--------+
          |
          | consumed by
          v
+------------------+
| demo / API / UI  |
| agents / CLI     |
+------------------+
```

## 7. Migration Plan

```text
1. Keep corus_v1 reducer behavior stable.
2. Add timpos primitives as a separate package.
3. Add Corus replay adapter for object_state_map -> artifact_status_map.
4. Add tests for primitive replay determinism and dependency direction.
5. Keep demo/product concepts under demo/.
6. Move demo material into demo/neara/ only once the UI/product experience stabilizes.
7. Keep deterministic Fasia packets in fasia/.
8. Revisit repo split once APIs and ownership stabilize.
```

## 8. Test Plan

Tests should prove:

```text
timpos ids are deterministic
timpos replay produces object_state_map
object heads expose current state
timpos has no corus_v1 or demo imports
corus_v1 has no demo imports
corus_v1 still derives from declared artifact statuses without timpos
corus_v1 can consume replay output through replay_adapter
fasia translates context and emits Objective / Implement / Validate packets
fasia does not import demo or runtime behavior
demo can use both timpos and corus_v1 without changing reducer output
```

## 9. Keeper

```text
Timpos preserves observed state over time.
Corus derives coordination flow from current artifact state.
Fasia structures context through translation.

Moments preserve history.
Heads expose state.
Reducers derive work.
Fasia translates context.

Objective projects goal state.
Implement projects production state.
Validate projects review state.
```
