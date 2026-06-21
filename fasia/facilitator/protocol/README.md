# Facilitator Protocol

The facilitator protocol is the agent-agnostic format for the Facilitator Fasia surface.

It is not Claude-specific.

It should be usable by:

```text
Claude skill packages
ChatGPT prompts
Codex-style agents
custom API workers
UI flows
other agentic delivery forms
```

## Contents

```text
facilitator.prompt.md
  Agent instruction for producing governed YAML output.

facilitator.schema.yaml
  Object grammar for admitted facilitator output.

facilitator.guardrails.yaml
  Transition policy: what is allowed to cross each engine transition.

docs/transition_guardrails.md
  Human-readable guardrail explanation.

examples/
  Example source input and expected YAML output.

tests/golden/
  Boundary cases that pressure the guardrails.
```

## Engine

```text
Origin
→ WorkItem
    ├─ ExecutionProjection: how / what
    └─ MeaningProjection: why / whom
→ Requirement
→ Surface
→ Outcome
→ Memory
```

## Guardrail rule

```text
The engine defines the transitions.
The guardrails define what is allowed to cross each transition.
The tests prove where the guardrails hold.
```

## Naming

This directory is called `protocol` instead of `contract` because it contains more than validation rules.

It includes:

```text
object grammar
prompt behavior
transition guardrails
examples
golden boundary tests
```

That makes it an agent-agnostic surface protocol.
