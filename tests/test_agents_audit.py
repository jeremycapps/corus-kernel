"""Audit tests — corus_agents is a workflow wrapper, not a second engine."""

from __future__ import annotations

import inspect
import re
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_agents import admission_agent, audit_agent, derive_agent, interpreter_agent, runner, surface_agent
from corus_agents.workflow import admission_required, derive_blocked_reason, review_required
from corus_kernel.schemas import ALLOWED_FIELDS, COLLECTION_KEYS

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"
AGENTS_DIR = Path(__file__).parent.parent / "corus_agents"

AGENT_FILES = (
    "__main__.py",
    "tasks.py",
    "runner.py",
    "workflow.py",
    "interpreter_agent.py",
    "admission_agent.py",
    "derive_agent.py",
    "audit_agent.py",
    "surface_agent.py",
)

FORBIDDEN_KERNEL_OBJECTS = re.compile(
    r"\b(rule|state_rule|resolution_state|commit)\b",
)
FORBIDDEN_SURFACE_OBJECT = re.compile(r'["\']surface["\']\s*:')


def _read_agent(name: str) -> str:
    return (AGENTS_DIR / name).read_text(encoding="utf-8")


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


# 1. interpreter_agent calls kernel interpretation


def test_interpreter_agent_calls_bootstrap_interpreter():
    source = inspect.getsource(interpreter_agent.run)
    assert "bootstrap" in source
    assert "corus_agents.bootstrap_interpreter" in inspect.getsource(interpreter_agent)


# 2. interpreter_agent writes candidates only


def test_interpreter_agent_does_not_import_derive():
    source = _read_agent("interpreter_agent.py")
    assert "derive_context" not in source
    assert "artifacts.yaml" not in source or "ADMITTED" in source


# 3–4. admission_agent compares and requires approval


def test_admission_agent_compares_candidates_to_admitted():
    source = inspect.getsource(admission_agent.build_report)
    assert "_compare_candidates" in source
    assert "ready_to_admit" in source


def test_admission_agent_promote_only_when_approve_true():
    source = inspect.getsource(admission_agent.run)
    assert "if approve:" in source
    assert "_promote_candidates" in source


# 5–6. derive_agent calls kernel derive, not candidates


def test_derive_agent_calls_kernel_derive_context():
    source = inspect.getsource(derive_agent.run)
    assert "derive_context" in source
    assert "corus_kernel.derive" in inspect.getsource(derive_agent)


def test_derive_agent_source_never_reads_candidate_yaml():
    source = _read_agent("derive_agent.py")
    assert "artifacts.candidate.yaml" not in source
    assert "contracts.candidate.yaml" not in source
    assert "yaml.safe_load" not in source
    assert "yaml.load" not in source


# 7. audit_agent validates invariants


def test_audit_agent_validates_kernel_invariants_not_new_context():
    source = _read_agent("audit_agent.py")
    assert "validate_schema" in source
    assert "validate_references" in source
    assert "validate_unique_ids" in source
    assert "derive_context" in source  # hash check only
    assert "ALLOWED_FIELDS" not in source


# 8. surface_agent renders derived JSON only


def test_surface_agent_renders_derived_json_only():
    source = _read_agent("surface_agent.py")
    assert "render_readout" in source
    assert "derive_context" not in source
    assert "write_interpretation" not in source
    assert "load_bundle" not in source


def test_surface_agent_writes_explain_md():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        derive_agent.run(tmp_path)
        result = surface_agent.run(tmp_path)
        assert result.outputs["readout_path"].endswith("explain.md")
        assert (tmp_path / "explain.md").exists()


# 9. runner stops when admission or review required


def _make_admitted_differ_from_interpretation(tmp_path: Path) -> None:
    """Admitted YAML that interpret will refresh via candidates."""
    (tmp_path / "artifacts.yaml").write_text("artifacts: []\n")
    (tmp_path / "contracts.yaml").write_text("contracts: []\n")


def test_runner_interpret_exits_when_admission_required():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        _make_admitted_differ_from_interpretation(tmp_path)
        code = runner.main(["run", "interpret", str(tmp_path)])
        assert code == 2
        assert admission_required(tmp_path)


def test_runner_admission_report_exits_when_review_required():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        _make_admitted_differ_from_interpretation(tmp_path)
        interpreter_agent.run(tmp_path)
        code = runner.main(["run", "admission-report", str(tmp_path)])
        assert code == 2
        assert review_required(tmp_path)


def test_runner_derive_blocked_when_admission_pending():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        _make_admitted_differ_from_interpretation(tmp_path)
        interpreter_agent.run(tmp_path)
        assert derive_blocked_reason(tmp_path) is not None
        code = runner.main(["run", "derive", str(tmp_path)])
        assert code == 2


def test_runner_derive_succeeds_after_explicit_admission():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_fixture(tmp_path)
        _make_admitted_differ_from_interpretation(tmp_path)
        interpreter_agent.run(tmp_path)
        admission_agent.run(tmp_path, approve=True)
        assert not review_required(tmp_path)
        code = runner.main(["run", "derive", str(tmp_path)])
        assert code == 0


# 10–11. No new declared types or forbidden kernel objects


def test_no_agent_file_defines_declared_object_types():
    for name in AGENT_FILES:
        source = _read_agent(name)
        assert '"agent"' not in source or "agent." in source
        for collection in COLLECTION_KEYS:
            if collection == "sources":
                continue
            assert f'"{collection}"' not in source or "outputs" in source


def test_no_agent_file_introduces_forbidden_kernel_objects():
    for name in AGENT_FILES:
        source = _read_agent(name)
        assert not FORBIDDEN_KERNEL_OBJECTS.search(source), name
        assert not FORBIDDEN_SURFACE_OBJECT.search(source), name
    assert "agent" not in ALLOWED_FIELDS


# derive isolation with only artifacts.candidate differing (no contracts.candidate gate)


def test_derive_agent_uses_admitted_not_artifact_candidate():
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

        result = derive_agent.run(tmp_path)
        output = derive_agent.load_output(Path(result.outputs["derive_output"]))
        statuses = {item["status"] for item in output["derived"]["artifact_statuses"]}
        assert "validated" not in statuses
