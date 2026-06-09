"""Tests for interpretation signals, bootstrap traces, and admission workflow."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_agents import admission_agent, derive_agent, interpreter_agent, runner
from corus_agents import interpretation_signals as signals
from corus_agents.bootstrap_interpreter import bootstrap
from corus_agents.source_text import load_source_text
from corus_kernel.schemas import ALLOWED_FIELDS

FIXTURE_V0 = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"
FIXTURE_SMOKE = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_smoke"

CVA_TEXT = (FIXTURE_V0 / "sources/text/source.neara_cva_job_description.txt").read_text()
FDE_TEXT = (FIXTURE_V0 / "sources/text/source.neara_fde_job_description.txt").read_text()
DIRECTOR_TEXT = (
    FIXTURE_V0 / "sources/text/source.neara_director_customer_implementation_job_description.txt"
).read_text()
RVO_TEXT = (FIXTURE_V0 / "sources/text/source.neara_rvo.txt").read_text()
DS_TEXT = (FIXTURE_V0 / "sources/text/source.neara_data_scientist_job_description.txt").read_text()

RVO_SOURCE = "source.neara_rvo"


def _copy_v0_without_admitted_artifacts(tmp_path: Path) -> None:
    for name in (
        "roles.yaml",
        "teams.yaml",
        "profiles.yaml",
        "boundaries.yaml",
        "moments.yaml",
        "timpos.yaml",
        "interpret_fixture.py",
    ):
        src = FIXTURE_V0 / name
        if src.exists():
            shutil.copy2(src, tmp_path / name)
    shutil.copytree(FIXTURE_V0 / "sources", tmp_path / "sources")


def _copy_v0_full(tmp_path: Path) -> None:
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
        src = FIXTURE_V0 / name
        if src.exists():
            shutil.copy2(src, tmp_path / name)
    shutil.copytree(FIXTURE_V0 / "sources", tmp_path / "sources")


# 1–5. Phrase matcher role-specific signals


def test_phrase_matcher_detects_cva_value_roi_signals():
    matched = signals.match_signals(CVA_TEXT)
    role_hits = signals.match_phrases(CVA_TEXT, signals.CVA_ARTIFACT_PHRASES)
    assert role_hits
    assert "business cases" in role_hits or "business case" in role_hits
    assert "roi metrics" in role_hits or "quantifiable roi" in role_hits
    assert matched.get("output_nouns") or matched.get("evidence_decision_language")
    assert signals.has_artifact_evidence(matched, signals.CVA_ARTIFACT_PHRASES, CVA_TEXT)


def test_phrase_matcher_detects_fde_technical_signals():
    matched = signals.match_signals(FDE_TEXT)
    role_hits = signals.match_phrases(FDE_TEXT, signals.FDE_ARTIFACT_PHRASES)
    assert role_hits
    assert any(p in role_hits for p in ("sdk", "api", "integrations", "technical design"))
    assert signals.has_artifact_evidence(matched, signals.FDE_ARTIFACT_PHRASES, FDE_TEXT)


def test_phrase_matcher_detects_director_orchestrator_signals():
    role_hits = signals.match_phrases(DIRECTOR_TEXT, signals.DIRECTOR_BOUNDARY_PHRASES)
    assert "orchestrator" in role_hits or "role for an orchestrator" in role_hits
    assert "living account strategy" in role_hits
    matched = signals.match_signals(DIRECTOR_TEXT)
    assert matched.get("coordination_handoff_language") or matched.get("ownership_maintenance_nouns")


def test_phrase_matcher_detects_rvo_boundary_subject_signals():
    role_hits = signals.match_phrases(RVO_TEXT, signals.RVO_BOUNDARY_PHRASES)
    assert "asset-level intelligence" in role_hits
    assert "intervention scenarios" in role_hits
    assert "cost-benefit" in role_hits or "cost benefit" in role_hits


def test_phrase_matcher_detects_data_scientist_future_signals():
    role_hits = signals.match_phrases(DS_TEXT, signals.DATA_SCIENTIST_FUTURE_PHRASES)
    assert "digital twin" in role_hits
    assert "wildfire risk" in role_hits
    assert "data pipeline" in role_hits or "data pipelines" in role_hits


# 6. Negative filters


def test_negative_filters_do_not_produce_artifacts():
    boilerplate = (
        "Strong communication skills. Competitive salary and benefits. "
        "Hybrid location in NYC. Low ego culture. Nice-to-have Python."
    )
    negatives = signals.match_negative_filters(boilerplate)
    assert "strong communication skills" in negatives
    assert "competitive salary" in negatives
    assert "hybrid" in negatives
    assert not signals.has_artifact_evidence(
        signals.match_signals(boilerplate),
        signals.CVA_ARTIFACT_PHRASES,
        boilerplate,
    )


# 7–9. Candidate trace richness


@pytest.fixture
def bootstrap_result(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("bootstrap")
    _copy_v0_without_admitted_artifacts(tmp)
    return bootstrap(tmp)


def test_candidate_trace_includes_matched_phrases_for_artifacts(bootstrap_result):
    trace = bootstrap_result["trace"]
    artifact_steps = [s for s in trace if s.get("action") == "derive_artifact"]
    assert len(artifact_steps) == 4
    for step in artifact_steps:
        assert step.get("matched_phrases")
        assert step.get("signal_groups")


def test_candidate_trace_includes_origin_and_subject(bootstrap_result):
    trace = bootstrap_result["trace"]
    for step in [s for s in trace if s.get("action") == "derive_artifact"]:
        assert step["origin"].startswith("source.")
        assert step["subject"] == RVO_SOURCE


def test_candidate_trace_marks_admission_required(bootstrap_result):
    trace = bootstrap_result["trace"]
    artifact_steps = [s for s in trace if s.get("action") == "derive_artifact"]
    contract_steps = [s for s in trace if s.get("action") == "derive_contract"]
    assert all(s.get("admission_required") is True for s in artifact_steps)
    assert all(s.get("admission_required") is True for s in contract_steps)


# 10. Admitted artifacts stay minimal


def test_admitted_artifacts_exclude_interpretation_evidence():
    artifacts = yaml.safe_load((FIXTURE_V0 / "artifacts.yaml").read_text())["artifacts"]
    forbidden = {"interpretation_basis", "matched_phrases", "signal_groups", "confidence"}
    for artifact in artifacts:
        assert forbidden.isdisjoint(artifact.keys())
        assert set(artifact.keys()).issubset(ALLOWED_FIELDS["artifact"])


# 11–15. Source relationship roles


def test_rvo_is_subject_not_origin(bootstrap_result):
    artifacts = bootstrap_result["artifacts"]
    for artifact in artifacts:
        assert artifact["subject"] == RVO_SOURCE
        assert artifact["origin"] != [RVO_SOURCE]
    rvo_class = next(
        c for c in bootstrap_result["bootstrap_report"]["source_classifications"]
        if c["source_id"] == RVO_SOURCE
    )
    assert rvo_class["relationship_role"] == "boundary_subject"


def test_cva_jd_is_origin_for_cva_artifacts(bootstrap_result):
    cva_origin = "source.neara_cva_job_description"
    cva_artifacts = [
        a for a in bootstrap_result["artifacts"] if cva_origin in a["origin"]
    ]
    assert {a["id"] for a in cva_artifacts} == {
        "artifact.value_evidence.rvo",
        "artifact.roi_case.rvo",
    }


def test_fde_jd_is_origin_for_fde_artifacts(bootstrap_result):
    fde_origin = "source.neara_fde_job_description"
    fde_artifacts = [
        a for a in bootstrap_result["artifacts"] if fde_origin in a["origin"]
    ]
    assert {a["id"] for a in fde_artifacts} == {
        "artifact.technical_evidence.rvo",
        "artifact.integration_path.rvo",
    }


def test_director_jd_supports_boundary_orchestrator(bootstrap_result):
    trace = bootstrap_result["trace"]
    director_step = next(
        s for s in trace
        if s.get("action") == "classify_source"
        and s.get("source_id") == "source.neara_director_customer_implementation_job_description"
    )
    assert director_step["relationship_role"] == "orchestrator_basis"
    assert director_step["supports_profile"] == "profile.neara_director_customer_implementation"
    boundary = bootstrap_result["bootstrap_report"]["candidate_boundary"][0]
    assert boundary["orchestrator"] == "profile.neara_director_customer_implementation"


def test_data_scientist_loaded_but_excluded_from_v0_team(bootstrap_result):
    report = bootstrap_result["bootstrap_report"]
    excluded = report["excluded_sources"]
    assert any(e["source_id"] == "source.neara_data_scientist_job_description" for e in excluded)
    team = report["candidate_team"][0]
    assert "role.neara_data_scientist" not in team["roles"]
    trace = bootstrap_result["trace"]
    assert any(s.get("action") == "exclude_source" for s in trace)


# 16. Bootstrap from raw produces candidates only


def test_bootstrap_from_raw_produces_declarations_and_candidates_only():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(FIXTURE_SMOKE / "sources", tmp_path / "sources")
        (tmp_path / "sources" / "sources.yaml").unlink()

        bootstrap(tmp_path)

        assert (tmp_path / "sources" / "sources.yaml").exists()
        assert (tmp_path / "artifacts.candidate.yaml").exists()
        assert (tmp_path / "bootstrap_report.json").exists()
        assert not (tmp_path / "artifacts.yaml").exists()


# 17. Derive never reads candidates before admission


def test_derive_never_uses_candidates_before_admission():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _copy_v0_full(tmp_path)
        interpreter_agent.run(tmp_path)

        admitted = yaml.safe_load((tmp_path / "artifacts.yaml").read_text())
        admitted["artifacts"][0]["status"] = "present"
        (tmp_path / "artifacts.yaml").write_text(yaml.dump(admitted))

        candidate = yaml.safe_load((tmp_path / "artifacts.candidate.yaml").read_text())
        for artifact in candidate["artifacts"]:
            artifact["status"] = "validated"
        (tmp_path / "artifacts.candidate.yaml").write_text(yaml.dump(candidate))
        # contracts.candidate.yaml omitted — derive gate checks both candidate files
        contracts_candidate = tmp_path / "contracts.candidate.yaml"
        if contracts_candidate.exists():
            contracts_candidate.unlink()

        derive_agent.run(tmp_path)
        output = derive_agent.load_output(tmp_path / "derive.output.json")
        statuses = {item["status"] for item in output["derived"]["artifact_statuses"]}
        assert "validated" not in statuses
        assert "present" in statuses


# 18. After admission pipeline completes


def test_after_admission_derive_audit_explain_complete():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(FIXTURE_SMOKE / "sources", tmp_path / "sources", symlinks=True)
        for name in (
            "roles.yaml",
            "teams.yaml",
            "profiles.yaml",
            "boundaries.yaml",
            "moments.yaml",
            "timpos.yaml",
        ):
            shutil.copy2(FIXTURE_SMOKE / name, tmp_path / name)

        runner.main(["run", str(tmp_path)])
        admission_agent.run(tmp_path, approve=True)
        code = runner.main(["run", str(tmp_path)])

        assert code == 0
        assert (tmp_path / "derive.output.json").exists()
        assert (tmp_path / "audit_report.json").exists()
        assert (tmp_path / "explain.md").exists()


def test_bootstrap_report_schema(bootstrap_result):
    report = bootstrap_result["bootstrap_report"]
    for key in (
        "source_files",
        "source_declarations",
        "source_classifications",
        "candidate_roles",
        "candidate_team",
        "candidate_profiles",
        "candidate_boundary",
        "candidate_artifacts",
        "candidate_contracts",
        "excluded_sources",
        "negative_filters_applied",
        "admission_required",
    ):
        assert key in report


def test_text_stubs_used_instead_of_pdf():
    text, status = load_source_text(
        FIXTURE_V0,
        "source.neara_cva_job_description",
        "sources/raw/Customer Value Architect - USA (NYC) @ Neara.pdf",
    )
    assert status == "text_stub"
    assert "business cases" in text.lower()


def test_build_source_signal_report_shape():
    report = signals.build_source_signal_report(
        "source.neara_cva_job_description", CVA_TEXT, "text_stub"
    )
    assert report["source_id"] == "source.neara_cva_job_description"
    assert "matched_signals" in report
    assert isinstance(report["matched_signals"], dict)
