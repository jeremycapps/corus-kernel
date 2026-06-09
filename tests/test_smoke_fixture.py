"""Smoke tests for fresh-source agent workflow fixture."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_agents import admission_agent, derive_agent, runner
from corus_agents.workflow import review_required
from corus_kernel.loader import DERIVE_BUNDLE_FILES

SMOKE_DIR = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_smoke"
V0_DIR = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"


def _copy_smoke_fixture(tmp_path: Path) -> Path:
    for name in (
        "roles.yaml",
        "teams.yaml",
        "profiles.yaml",
        "boundaries.yaml",
        "moments.yaml",
        "timpos.yaml",
        "interpret_fixture.py",
    ):
        shutil.copy2(SMOKE_DIR / name, tmp_path / name)
    shutil.copytree(SMOKE_DIR / "sources", tmp_path / "sources", symlinks=True)
    return tmp_path


def test_smoke_fixture_has_no_admitted_artifacts_or_contracts():
    assert not (SMOKE_DIR / "artifacts.yaml").exists()
    assert not (SMOKE_DIR / "contracts.yaml").exists()
    assert (SMOKE_DIR / "sources" / "sources.yaml").exists()
    assert (SMOKE_DIR / "interpret_fixture.py").exists()


def test_fresh_fixture_stops_before_derive():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = _copy_smoke_fixture(Path(tmp))
        code = runner.main(["run", str(tmp_path)])

        assert code == 2
        assert (tmp_path / "artifacts.candidate.yaml").exists()
        assert (tmp_path / "contracts.candidate.yaml").exists()
        assert (tmp_path / "admission_report.json").exists()
        assert not (tmp_path / "derive.output.json").exists()
        assert not (tmp_path / "artifacts.yaml").exists()
        assert not (tmp_path / "contracts.yaml").exists()


def test_fresh_fixture_produces_candidate_files():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = _copy_smoke_fixture(Path(tmp))
        runner.main(["run", str(tmp_path)])

        artifacts = yaml.safe_load(
            (tmp_path / "artifacts.candidate.yaml").read_text(encoding="utf-8")
        )
        contracts = yaml.safe_load(
            (tmp_path / "contracts.candidate.yaml").read_text(encoding="utf-8")
        )
        assert len(artifacts["artifacts"]) == 4
        assert len(contracts["contracts"]) == 4


def test_admission_requires_explicit_approve():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = _copy_smoke_fixture(Path(tmp))
        runner.main(["run", str(tmp_path)])

        code = runner.main(["admit", str(tmp_path)])
        assert code == 2
        assert not (tmp_path / "artifacts.yaml").exists()

        admission_agent.run(tmp_path, approve=True)
        assert (tmp_path / "artifacts.yaml").exists()
        assert (tmp_path / "contracts.yaml").exists()
        assert (
            (tmp_path / "artifacts.yaml").read_text(encoding="utf-8")
            == (tmp_path / "artifacts.candidate.yaml").read_text(encoding="utf-8")
        )


def test_after_admission_pipeline_completes_derive_audit_explain():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = _copy_smoke_fixture(Path(tmp))
        runner.main(["run", str(tmp_path)])
        runner.main(["admit", str(tmp_path), "--approve"])
        assert not review_required(tmp_path)

        code = runner.main(["run", str(tmp_path)])
        assert code == 0
        assert (tmp_path / "derive.output.json").exists()
        assert (tmp_path / "audit_report.json").exists()
        assert (tmp_path / "explain.md").exists()

        output = json.loads((tmp_path / "derive.output.json").read_text(encoding="utf-8"))
        assert output["derived"]["context_state"]["coordination"] == "unresolved"
        assert output["derived"]["context_state"]["reason"] == "missing_or_rejected_artifacts"


def test_explain_md_contains_cva_fde_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = _copy_smoke_fixture(Path(tmp))
        runner.main(["run", str(tmp_path)])
        runner.main(["admit", str(tmp_path), "--approve"])
        runner.main(["run", str(tmp_path)])

        explain = (tmp_path / "explain.md").read_text(encoding="utf-8")
        assert "artifact.value_evidence.rvo" in explain
        assert "artifact.roi_case.rvo" in explain
        assert "artifact.technical_evidence.rvo" in explain
        assert "artifact.integration_path.rvo" in explain
        assert "expected_missing" in explain


def test_derive_never_reads_candidate_files_in_smoke_workflow():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = _copy_smoke_fixture(Path(tmp))
        runner.main(["run", str(tmp_path)])
        runner.main(["admit", str(tmp_path), "--approve"])

        admitted = yaml.safe_load((tmp_path / "artifacts.yaml").read_text())
        admitted["artifacts"][0]["status"] = "present"
        (tmp_path / "artifacts.yaml").write_text(yaml.dump(admitted))

        candidate = yaml.safe_load((tmp_path / "artifacts.candidate.yaml").read_text())
        for artifact in candidate["artifacts"]:
            artifact["status"] = "validated"
        (tmp_path / "artifacts.candidate.yaml").write_text(yaml.dump(candidate))

        derive_agent.run(tmp_path)
        output = derive_agent.load_output(tmp_path / "derive.output.json")
        statuses = {item["status"] for item in output["derived"]["artifact_statuses"]}
        assert "validated" not in statuses
        assert "present" in statuses

    for filename in DERIVE_BUNDLE_FILES.values():
        assert "candidate" not in filename
