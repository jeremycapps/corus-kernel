# Libera Claude Delivery

This directory is the Claude-specific delivery package for Libera.

Libera is the intake and proposal layer. Claude delivery may add commands, skill guidance, and examples, but it should not redefine the Libera protocol objects.

Source of truth:

- `libera.prompt.md`
- `libera.schema.yaml`
- `libera.guardrails.yaml`

Keeper:

Protocol is agent-agnostic. Claude is one delivery implementation.
