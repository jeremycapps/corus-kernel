"""Tests proving kernel logic is generic, not Neara-hard-coded."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import yaml

from corus_kernel.derive import derive_context
from corus_kernel.interpret import interpret_sources

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"
KERNEL_DIR = Path(__file__).parent.parent / "corus_kernel"

NEARA_TERMS = re.compile(
    r"\b(RVO|CVA|FDE|Director|Data Scientist|Neara)\b",
    re.IGNORECASE,
)
NEARA_SOURCE_IDS = re.compile(r"source\.neara_")


def test_derive_module_has_no_neara_string_constants():
    source = (KERNEL_DIR / "derive.py").read_text(encoding="utf-8")
    assert not NEARA_TERMS.search(source)


def test_interpret_module_has_no_neara_source_ids():
    source = (KERNEL_DIR / "interpret.py").read_text(encoding="utf-8")
    assert not NEARA_SOURCE_IDS.search(source)


def test_interpret_module_has_no_rule_object():
    source = (KERNEL_DIR / "interpret.py").read_text(encoding="utf-8")
    assert "interpretation_rules" not in source
    assert "load_interpretation_rules" not in source
    assert "skip_rule" not in source
    assert "rule_id" not in source


def test_derive_module_does_not_load_interpretation_config():
    source = (KERNEL_DIR / "derive.py").read_text(encoding="utf-8")
    assert "interpret_fixture" not in source
    assert "interpretation_rules" not in source


def test_neara_fixture_interpreter_produces_expected_candidates():
    result = interpret_sources(FIXTURE_DIR)
    artifact_ids = {a["id"] for a in result["artifacts"]}
    contract_ids = {c["id"] for c in result["contracts"]}
    assert artifact_ids == {
        "artifact.value_evidence.rvo",
        "artifact.roi_case.rvo",
        "artifact.technical_evidence.rvo",
        "artifact.integration_path.rvo",
    }
    assert contract_ids == {
        "contract.cva.value_evidence.rvo",
        "contract.cva.roi_case.rvo",
        "contract.fde.technical_evidence.rvo",
        "contract.fde.integration_path.rvo",
    }


def test_answer_changes_when_artifact_statuses_change():
    unresolved = derive_context(FIXTURE_DIR)
    assert unresolved["derived"]["context_state"]["coordination"] == "unresolved"
    assert "unresolved" in unresolved["answer"] or "expected_missing" in unresolved["answer"]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in (
            "artifacts.yaml",
            "contracts.yaml",
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

        admitted = yaml.safe_load((FIXTURE_DIR / "artifacts.yaml").read_text())
        for artifact in admitted["artifacts"]:
            artifact["status"] = "present"
        (tmp_path / "artifacts.yaml").write_text(yaml.dump(admitted))

        ready = derive_context(tmp_path)
        assert ready["derived"]["context_state"]["coordination"] == "ready"
        assert ready["answer"] != unresolved["answer"]
        assert "ready" in ready["answer"]


def test_missing_boundary_subject_derives_blocked_context():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in (
            "artifacts.yaml",
            "contracts.yaml",
            "roles.yaml",
            "teams.yaml",
            "profiles.yaml",
            "moments.yaml",
            "timpos.yaml",
        ):
            (tmp_path / name).write_text((FIXTURE_DIR / name).read_text())
        (tmp_path / "sources").mkdir()
        (tmp_path / "sources" / "sources.yaml").write_text(
            (FIXTURE_DIR / "sources" / "sources.yaml").read_text()
        )

        boundaries = yaml.safe_load((FIXTURE_DIR / "boundaries.yaml").read_text())
        boundaries["boundaries"][0]["subject"] = None
        (tmp_path / "boundaries.yaml").write_text(yaml.dump(boundaries))

        output = derive_context(tmp_path)
        assert output["derived"]["context_state"]["coordination"] == "blocked"
        assert output["derived"]["context_state"]["reason"] == "missing_subject"
        assert any("subject missing" in w for w in output["warnings"])


def test_derive_boundary_flag_selects_by_id():
    output = derive_context(
        FIXTURE_DIR,
        boundary_id="boundary.neara.rvo.account_context",
    )
    assert (
        output["derived"]["contexts"][0]["boundary_id"]
        == "boundary.neara.rvo.account_context"
    )
