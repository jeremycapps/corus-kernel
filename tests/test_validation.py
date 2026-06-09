"""Kernel validation and resolution audit tests."""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_kernel.derive import derive_context, derive_context_for_state
from corus_kernel.loader import load_bundle
from corus_kernel.schemas import ALLOWED_FIELDS, COLLECTION_KEYS, REQUIRED_FIELDS
from corus_kernel.validate import (
    ValidationError,
    validate_schema,
    validate_unique_ids,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"
KERNEL_DIR = Path(__file__).parent.parent / "corus_kernel"


def _bundle_with(**overrides: list[dict]) -> dict:
    bundle = load_bundle(FIXTURE_DIR)
    for key, value in overrides.items():
        bundle[key] = value
    return bundle


def test_missing_required_field_fails():
    bundle = load_bundle(FIXTURE_DIR)
    bad = copy.deepcopy(bundle)
    del bad["sources"][0]["locator"]
    with pytest.raises(ValidationError, match="missing fields"):
        validate_schema(bad)


def test_invalid_source_type_fails():
    bundle = load_bundle(FIXTURE_DIR)
    bad = copy.deepcopy(bundle)
    bad["sources"][0]["type"] = "pdf"
    with pytest.raises(ValidationError, match="invalid type"):
        validate_schema(bad)


def test_invalid_artifact_status_fails():
    bundle = load_bundle(FIXTURE_DIR)
    bad = copy.deepcopy(bundle)
    bad["artifacts"][0]["status"] = "unknown"
    with pytest.raises(ValidationError, match="invalid status"):
        validate_schema(bad)


def test_invalid_profile_type_fails():
    bundle = load_bundle(FIXTURE_DIR)
    bad = copy.deepcopy(bundle)
    bad["profiles"][0]["type"] = "person"
    with pytest.raises(ValidationError, match="invalid type"):
        validate_schema(bad)


def test_profile_type_team_resolves_to_team():
    bundle = load_bundle(FIXTURE_DIR)
    bundle["profiles"].append(
        {
            "id": "profile.neara_account_team",
            "type": "team",
            "ref": "team.neara_account_team",
        }
    )
    validate_schema(bundle)
    from corus_kernel.validate import validate_references

    validate_references(bundle)


def test_profile_type_team_invalid_ref_fails():
    bundle = load_bundle(FIXTURE_DIR)
    bundle["profiles"].append(
        {
            "id": "profile.missing_team",
            "type": "team",
            "ref": "team.does_not_exist",
        }
    )
    from corus_kernel.validate import validate_references

    with pytest.raises(ValidationError, match="ref team.does_not_exist not found"):
        validate_references(bundle)


def test_duplicate_ids_within_collection_fail():
    bundle = load_bundle(FIXTURE_DIR)
    bad = copy.deepcopy(bundle)
    bad["roles"].append(copy.deepcopy(bad["roles"][0]))
    with pytest.raises(ValidationError, match="duplicate id"):
        validate_unique_ids(bad)


def test_duplicate_ids_across_collections_fail():
    bundle = load_bundle(FIXTURE_DIR)
    bad = copy.deepcopy(bundle)
    bad["contracts"][0]["id"] = bad["artifacts"][0]["id"]
    with pytest.raises(ValidationError, match="duplicate id"):
        validate_unique_ids(bad)


def test_boundary_subject_ref_missing_produces_blocked_context():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in (
            "roles.yaml",
            "teams.yaml",
            "profiles.yaml",
            "boundaries.yaml",
            "timpos.yaml",
        ):
            (tmp_path / name).write_text((FIXTURE_DIR / name).read_text())
        (tmp_path / "sources").mkdir()
        sources = yaml.safe_load((FIXTURE_DIR / "sources" / "sources.yaml").read_text())
        sources["sources"] = [
            s for s in sources["sources"] if s["id"] != "source.neara_rvo"
        ]
        (tmp_path / "sources" / "sources.yaml").write_text(yaml.dump(sources))
        (tmp_path / "artifacts.yaml").write_text("artifacts: []\n")
        (tmp_path / "contracts.yaml").write_text("contracts: []\n")
        (tmp_path / "moments.yaml").write_text("moments: []\n")

        output = derive_context(tmp_path)
        assert output["derived"]["context_state"]["coordination"] == "blocked"
        assert output["derived"]["context_state"]["reason"] == "missing_subject"
        assert any(
            "subject source.neara_rvo not found; context blocked" in w
            for w in output["warnings"]
        )


def test_boundary_zero_selected_artifacts_produces_no_selected_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in (
            "artifacts.yaml",
            "roles.yaml",
            "teams.yaml",
            "profiles.yaml",
            "boundaries.yaml",
            "moments.yaml",
            "timpos.yaml",
        ):
            (tmp_path / name).write_text((FIXTURE_DIR / name).read_text())
        (tmp_path / "sources").mkdir()
        (tmp_path / "sources" / "sources.yaml").write_text(
            (FIXTURE_DIR / "sources" / "sources.yaml").read_text()
        )
        (tmp_path / "contracts.yaml").write_text("contracts: []\n")

        output = derive_context(tmp_path)
        assert output["derived"]["context_state"]["coordination"] == "unresolved"
        assert output["derived"]["context_state"]["reason"] == "no_selected_artifacts"


def test_no_selected_artifacts_via_reducer():
    boundary = {"id": "b", "subject": "source.neara_rvo", "team": "team.neara_account_team"}
    state = derive_context_for_state(boundary, [])
    assert state["reason"] == "no_selected_artifacts"


def test_fixture_interpreter_not_in_schemas():
    assert "interpret_fixture" not in ALLOWED_FIELDS
    assert "interpret_fixture" not in REQUIRED_FIELDS
    assert "interpret_fixture" not in COLLECTION_KEYS
    assert "rule" not in ALLOWED_FIELDS
    assert "rule" not in REQUIRED_FIELDS
    assert "rule" not in COLLECTION_KEYS


def test_schemas_define_required_fields_for_all_object_types():
    for object_type in ALLOWED_FIELDS:
        assert object_type in REQUIRED_FIELDS
        assert REQUIRED_FIELDS[object_type] <= ALLOWED_FIELDS[object_type]


def test_kernel_modules_do_not_define_rule_object():
    for name in ("schemas.py", "validate.py", "derive.py", "interpret.py", "loader.py"):
        source = (KERNEL_DIR / name).read_text(encoding="utf-8")
        assert '"rule"' not in source
        assert "'rule'" not in source or "skip_rule" not in source
