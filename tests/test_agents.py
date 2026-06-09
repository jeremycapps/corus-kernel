"""Tests for corus_agents runtime layer."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_agents import admission_agent, audit_agent, derive_agent, interpreter_agent, surface_agent
from corus_agents.tasks import AGENT_VERBS, build_moment
from corus_kernel.loader import DERIVE_BUNDLE_FILES, load_bundle
from corus_kernel.schemas import ALLOWED_FIELDS, COLLECTION_KEYS
from corus_kernel.validate import validate_schema

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"


def _copy_fixture(tmp_path: Path) -> None:
    for name in (
        "artifacts.yaml",
        "contracts.yaml",
        "roles.yaml",
        "teams.yaml",
        "profiles.yaml",
        "boundaries.yaml",
        "moments.yaml",
        "timpos.yaml",
        "interpret_fixture.py",
    ):
        src = FIXTURE_DIR / name
        if src.exists():
            shutil.copy2(src, tmp_path / name)
    shutil.copytree(FIXTURE_DIR / "sources", tmp_path / "sources")


# 1. Agents do not add new declared object types


def test_agents_do_not_add_declared_object_types():
    assert "agent" not in ALLOWED_FIELDS
    assert "agent" not in COLLECTION_KEYS
    for filename in DERIVE_BUNDLE_FILES.values():
        assert "agent" not in filename


# 2. Interpreter Agent writes candidates only


def test_interpreter_agent_writes_candidates_only():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        admitted_artifacts = (tmp_path / "artifacts.yaml").read_text(encoding="utf-8")
        admitted_contracts = (tmp_path / "contracts.yaml").read_text(encoding="utf-8")

        result = interpreter_agent.run(tmp_path)

        assert (tmp_path / "artifacts.candidate.yaml").exists()
        assert (tmp_path / "contracts.candidate.yaml").exists()
        assert (tmp_path / "interpretation_trace.json").exists()
        assert (tmp_path / "artifacts.yaml").read_text(encoding="utf-8") == admitted_artifacts
        assert (tmp_path / "contracts.yaml").read_text(encoding="utf-8") == admitted_contracts
        assert result.outputs["artifact_count"] == 4
        assert result.verb == "agent.interpret"


# 3. Derive Agent never reads candidate files


def test_derive_agent_never_reads_candidate_files():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)

        admitted = yaml.safe_load((tmp_path / "artifacts.yaml").read_text())
        admitted["artifacts"][0]["status"] = "present"
        (tmp_path / "artifacts.yaml").write_text(yaml.dump(admitted))

        candidate = yaml.safe_load((FIXTURE_DIR / "artifacts.yaml").read_text())
        for artifact in candidate["artifacts"]:
            artifact["status"] = "validated"
        (tmp_path / "artifacts.candidate.yaml").write_text(yaml.dump(candidate))
        # contracts.candidate.yaml omitted — derive gate checks both candidates

        result = derive_agent.run(tmp_path)
        output = derive_agent.load_output(Path(result.outputs["derive_output"]))

        statuses = {
            item["status"]
            for item in output["derived"]["artifact_statuses"]
        }
        assert "validated" not in statuses
        assert output["derived"]["context_state"]["coordination"] == "unresolved"


# 4. Admission Agent requires explicit approval to promote


def test_admission_agent_report_without_promotion():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        interpreter_agent.run(tmp_path)
        admitted_before = (tmp_path / "artifacts.yaml").read_text(encoding="utf-8")

        result = admission_agent.run(tmp_path, approve=False)

        assert (tmp_path / "admission_report.json").exists()
        assert result.outputs["promoted"] is False
        assert (tmp_path / "artifacts.yaml").read_text(encoding="utf-8") == admitted_before


def test_admission_agent_promotes_only_with_approve():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        interpreter_agent.run(tmp_path)

        candidates = (tmp_path / "artifacts.candidate.yaml").read_text(encoding="utf-8")
        admission_agent.run(tmp_path, approve=True)

        assert (tmp_path / "artifacts.yaml").read_text(encoding="utf-8") == candidates


# 5. Audit Agent reports failures without mutating files


def test_audit_agent_passes_valid_fixture():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        snapshot = {
            name: (tmp_path / name).read_text(encoding="utf-8")
            for name in ("artifacts.yaml", "contracts.yaml", "boundaries.yaml")
        }

        result = audit_agent.run(tmp_path)

        assert result.outputs["passed"] is True
        for name, content in snapshot.items():
            assert (tmp_path / name).read_text(encoding="utf-8") == content


def test_audit_agent_reports_failures_without_mutation():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        artifacts = yaml.safe_load((tmp_path / "artifacts.yaml").read_text())
        artifacts["artifacts"][0]["status"] = "invalid_status"
        (tmp_path / "artifacts.yaml").write_text(yaml.dump(artifacts))
        before = (tmp_path / "artifacts.yaml").read_text(encoding="utf-8")

        result = audit_agent.run(tmp_path)

        assert result.outputs["passed"] is False
        assert (tmp_path / "audit_report.json").exists()
        assert (tmp_path / "artifacts.yaml").read_text(encoding="utf-8") == before


# 6. Surface Agent renders from derived JSON only


def test_surface_agent_renders_from_derived_json():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        derive_result = derive_agent.run(tmp_path)

        admitted_before = load_bundle(tmp_path)
        readout_result = surface_agent.run(
            tmp_path,
            derive_path=Path(derive_result.outputs["derive_output"]),
        )
        admitted_after = load_bundle(tmp_path)

        readout = readout_result.outputs["readout"]
        assert "Summary" in readout
        assert "Coordination" in readout
        assert admitted_before == admitted_after


def test_surface_agent_does_not_call_derive_when_output_supplied():
    derive_output = derive_agent.load_output(FIXTURE_DIR / "golden" / "derive.json")
    readout = surface_agent.render_readout(derive_output)
    assert derive_output["answer"] in readout
    assert "Trace" in readout


# 7. Agent actions represented as moments


@pytest.mark.parametrize("verb", sorted(AGENT_VERBS))
def test_agent_verbs_map_to_valid_moments(verb: str):
    moment = build_moment(verb, "object.example")
    assert set(moment.keys()) == {"id", "timpo", "actor", "via", "object", "previous"}
    assert moment["via"] == verb
    assert moment["actor"].startswith("profile.")
    validate_schema({"moments": [moment], **{k: [] for k in COLLECTION_KEYS}})


def test_interpreter_agent_returns_moment():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        result = interpreter_agent.run(tmp_path)
        assert result.moment is not None
        assert result.moment["via"] == "agent.interpret"
        assert result.moment["actor"] == "profile.corus_resolver"


def test_derive_agent_returns_moment():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        admission_agent.run(tmp_path, approve=False)
        result = derive_agent.run(tmp_path)
        assert result.moment["via"] == "agent.derive"
