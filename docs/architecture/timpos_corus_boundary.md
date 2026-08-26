# Timpos / Corus / Fasia Boundary

## 1. Conceptual Separation

Timpos preserves observed state over time.

Corus derives coordination flow from current artifact state.

Fasia structures context through Relations.

The keeper:

```text
Moment records.
Contract coordinates.
Relation contextualizes.
```

Current stack:

```text
Timpos remembers.
Corus coordinates.
Fasia contextualizes.
Agents act.
Renderers display.
```

Timpos is the primitive replay layer. It records observations and exposes the current state of opaque objects. It does not know what those objects mean.

Corus is the coordination layer. It consumes current artifact status, validates declared coordination objects, and derives readiness, output state, objective satisfaction, and next work.

Fasia is the relation layer. Its primitive is Relation: id, initiator, target, sources, and objectives. Relation existence is authored; path state is derived. Its first structured packet outputs are Objective, Implement, and Validate packets over Corus flow.

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
  deterministic relations, translation, and packets
```

Allowed dependency direction:

```text
demo -> corus_v1
demo -> timpos
demo -> fasia
corus_v1 -> timpos only through adapter-shaped data
timpos -> standard library only
```

Fasia imports nothing from the other layers. Corus flow, node states, artifact
statuses, admitted sources, and active objectives all arrive as explicit
arguments, so Fasia stays deterministic over inputs it did not fetch. Data
flows `corus_v1 -> fasia`; imports do not.

Forbidden direction:

```text
timpos -> corus_v1
timpos -> demo
timpos -> fasia
corus_v1 -> demo
corus_v1 -> fasia
fasia -> corus_v1
fasia -> timpos
fasia -> demo
fasia -> UI components
fasia -> agent runtime behavior
```

Enforced by `test_fasia_consumes_readiness_only_through_explicit_inputs`,
`test_corus_v1_does_not_import_fasia`, `test_timpos_has_no_corus_imports`, and
`test_timpos_has_no_demo_imports`.

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

Fasia structures context through Relations.

The primitive relation shape is:

```text
Relation = id + initiator + target + sources[] + objectives[]
```

A derived relation path is computed:

```text
DerivedRelation = relation + path + label + reasons[]
path = open | closed
```

Translation is what Fasia does. Relation is what Fasia declares. Path state is what Fasia derives.

## 7. Fasia Translation Modes v0

Relation declares a contextual edge.

Path says whether that edge can currently count.

Translation mode says what movement of context the edge supports.

The forward translation loop is:

```text
consumer -> discovery -> objective
objective -> strategy -> value
value -> product -> consumer
```

Definitions:

```text
Discovery translates consumer context into what should be pursued.
Strategy translates objective into why it matters.
Product translates value back into something usable by the consumer.
```

Keeper:

```text
Relations connect.
Paths open.
Translations move context.
```

Translation modes are Fasia vocabulary. Automatic mode derivation requires
stable node role conventions, such as `consumer.* -> objective.*`,
`objective.* -> value.*`, and `value.* -> consumer.*`. Fasia v0 does not add a
`Relation.mode` field.

Packets are above this layer.

UI/rendering is above this layer.

Agent runtime is above this layer.

## 8. Fasia Packet Boundary

Fasia packets are structured outputs over relations and Corus flow. They are not the whole of Fasia.

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
must not import `fasia`. `fasia` must not import `corus_v1`, `timpos`, demo, or
agent runtime behavior; it receives flow and state as explicit arguments.

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
          | relation translation / packet projection
          v
+------------------+
|      fasia       |
|------------------|
| Relation         |
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

## 9. Migration Plan

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

## 10. Test Plan

Tests should prove:

```text
timpos ids are deterministic
timpos replay produces object_state_map
object heads expose current state
timpos has no corus_v1 or demo imports
corus_v1 has no demo imports
corus_v1 still derives from declared artifact statuses without timpos
corus_v1 can consume replay output through replay_adapter
fasia contextualizes with Relations and emits Objective / Implement / Validate packets
fasia does not import corus_v1, timpos, demo, or runtime behavior
demo can use both timpos and corus_v1 without changing reducer output
```

## 11. Keeper

```text
Timpos preserves observed state over time.
Corus derives coordination flow from current artifact state.
Fasia structures context through Relations.

Moments preserve history.
Heads expose state.
Reducers derive work.
Fasia contextualizes.

Moments make time addressable.
Contracts make obligation addressable.
Relations make context addressable.

Requires gates nodes.
Relations connect nodes.
Sources ground relations.
Objectives scope relations.
Paths are derived.

Relations connect.
Paths open.
Translations move context.

Relation declares possibility.
Path says whether it can count.
Translation says what movement of context it supports.

Objective projects goal state.
Implement projects production state.
Validate projects review state.
```
