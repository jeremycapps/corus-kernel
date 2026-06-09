"""Allowed fields for declared object types."""

ALLOWED_FIELDS = {
    "source": {"id", "type", "label", "locator"},
    "artifact": {"id", "type", "label", "origin", "subject", "status"},
    "contract": {"id", "label", "owner", "artifact"},
    "role": {"id", "label"},
    "team": {"id", "label", "roles"},
    "profile": {"id", "type", "ref"},
    "boundary": {"id", "label", "orchestrator", "team", "subject"},
    "moment": {"id", "timpo", "actor", "via", "object", "previous"},
    "timpo": {"id", "t", "p"},
}

COLLECTION_KEYS = {
    "sources": "source",
    "artifacts": "artifact",
    "contracts": "contract",
    "roles": "role",
    "teams": "team",
    "profiles": "profile",
    "boundaries": "boundary",
    "moments": "moment",
    "timpos": "timpo",
}

MOMENT_FIELDS = ALLOWED_FIELDS["moment"]
