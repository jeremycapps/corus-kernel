"""Tests for Corus Kernel v0."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_kernel.derive import (
    derive_context,
    derive_context_for_state,
    derive_contract_status,
)
from corus_kernel.hash import sha256_hex
from corus_kernel.interpret import interpret_sources, write_interpretation
from corus_kernel.loader import load_bundle, load_sources
from corus_kernel.schemas import ALLOWED_FIELDS, MOMENT_FIELDS
from corus_kernel.validate import ValidationError, validate_bundle, validate_minimalism

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"

RVO_SOURCE = "source.neara_rvo"
CVA_SOURCE = "source.neara_cva_job_description"
FDE_SOURCE = "source.neara_fde_job_description"
DIRECTOR_SOURCE = "source.neara_director_customer_implementation_job_description"
DATA_SCIENTIST_SOURCE = "source.neara_data_scientist_job_description"


# 1. Declared object minimalism


def test_declared_object_minimalism_fixture_passes():
    bundle = load_bundle(FIXTURE_DIR)
    validate_minimalism(bundle)


def test_declared_object_minimalism_rejects_extra_fields():
    bundle = load_bundle(FIXTURE_DIR)
    bad = copy.deepcopy(bundle)
    bad["artifacts"][0]["derived_from"] = "source.neara_rvo"
    with pytest.raises(ValidationError, match="extra fields"):
        validate_minimalism(bad)


def test_all_object_types_have_allowed_field_sets():
    for object_type, fields in ALLOWED_FIELDS.items():
        assert "id" in fields
        assert len(fields) <= 6


# 2. Source loading


def test_source_loading_from_sources_yaml():
    sources = load_sources(FIXTURE_DIR)
    assert len(sources) == 5
    ids = {s["id"] for s in sources}
    assert RVO_SOURCE in ids
    assert CVA_SOURCE in ids
    assert FDE_SOURCE in ids
    assert DIRECTOR_SOURCE in ids
    assert DATA_SCIENTIST_SOURCE in ids


def test_source_locators_point_to_raw_pdfs():
    sources = load_sources(FIXTURE_DIR)
    for source in sources:
        locator = source["locator"]
        assert locator.startswith("sources/raw/")
        pdf_path = FIXTURE_DIR / locator
        assert pdf_path.exists(), f"Missing PDF: {pdf_path}"


# 3. Interpretation produces candidates


def test_interpretation_produces_candidate_artifacts_and_contracts():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "sources").mkdir()
        sources_data = yaml.safe_load(
            (FIXTURE_DIR / "sources" / "sources.yaml").read_text()
        )
        with (tmp_path / "sources" / "sources.yaml").open("w") as f:
            yaml.dump(sources_data, f)
        (tmp_path / "interpret_fixture.py").write_text(
            (FIXTURE_DIR / "interpret_fixture.py").read_text()
        )

        result = write_interpretation(tmp_path)
        assert (tmp_path / "artifacts.candidate.yaml").exists()
        assert (tmp_path / "contracts.candidate.yaml").exists()
        assert (tmp_path / "interpretation_trace.json").exists()
        assert len(result["artifacts"]) == 4
        assert len(result["contracts"]) == 4


def test_interpretation_expected_artifacts():
    result = interpret_sources(FIXTURE_DIR)
    artifact_ids = {a["id"] for a in result["artifacts"]}
    assert artifact_ids == {
        "artifact.value_evidence.rvo",
        "artifact.roi_case.rvo",
        "artifact.technical_evidence.rvo",
        "artifact.integration_path.rvo",
    }
    for artifact in result["artifacts"]:
        assert artifact["status"] == "expected_missing"
        assert artifact["subject"] == RVO_SOURCE


def test_interpretation_expected_contracts():
    result = interpret_sources(FIXTURE_DIR)
    contract_ids = {c["id"] for c in result["contracts"]}
    assert contract_ids == {
        "contract.cva.value_evidence.rvo",
        "contract.cva.roi_case.rvo",
        "contract.fde.technical_evidence.rvo",
        "contract.fde.integration_path.rvo",
    }


# 4. RVO is boundary subject, not artifact origin


def test_rvo_is_boundary_subject_not_artifact_origin():
    bundle = load_bundle(FIXTURE_DIR)
    boundary = bundle["boundaries"][0]
    assert boundary["subject"] == RVO_SOURCE

    for artifact in bundle["artifacts"]:
        assert RVO_SOURCE not in artifact.get("origin", [])
        assert artifact["subject"] == RVO_SOURCE


# 5. CVA JD is artifact origin for CVA artifacts


def test_cva_jd_is_origin_for_cva_artifacts():
    bundle = load_bundle(FIXTURE_DIR)
    cva_artifacts = [
        a for a in bundle["artifacts"] if a["type"] in ("value_evidence", "roi_case")
    ]
    assert len(cva_artifacts) == 2
    for artifact in cva_artifacts:
        assert CVA_SOURCE in artifact["origin"]


# 6. FDE JD is artifact origin for FDE artifacts


def test_fde_jd_is_origin_for_fde_artifacts():
    bundle = load_bundle(FIXTURE_DIR)
    fde_artifacts = [
        a
        for a in bundle["artifacts"]
        if a["type"] in ("technical_evidence", "integration_path")
    ]
    assert len(fde_artifacts) == 2
    for artifact in fde_artifacts:
        assert FDE_SOURCE in artifact["origin"]


# 7. Director JD supports orchestrator but creates no v0 artifacts


def test_director_jd_supports_orchestrator_no_artifacts():
    result = interpret_sources(FIXTURE_DIR)
    director_steps = [
        s for s in result["trace"] if s.get("source_id") == DIRECTOR_SOURCE
    ]
    assert any(s.get("role") == "orchestrator_basis" for s in director_steps)

    bundle = load_bundle(FIXTURE_DIR)
    boundary = bundle["boundaries"][0]
    assert boundary["orchestrator"] == "profile.neara_director_customer_implementation"

    for artifact in bundle["artifacts"]:
        assert DIRECTOR_SOURCE not in artifact.get("origin", [])


# 8. Data Scientist source loaded but excluded from v0


def test_data_scientist_source_loaded_but_excluded():
    sources = load_sources(FIXTURE_DIR)
    assert any(s["id"] == DATA_SCIENTIST_SOURCE for s in sources)

    teams = load_bundle(FIXTURE_DIR)["teams"]
    team_roles = set(teams[0]["roles"])
    assert "role.neara_data_scientist" not in team_roles

    result = interpret_sources(FIXTURE_DIR)
    exclude_steps = [
        s for s in result["trace"] if s.get("action") == "exclude_source"
    ]
    assert len(exclude_steps) == 1
    assert exclude_steps[0]["source_id"] == DATA_SCIENTIST_SOURCE

    for artifact in result["artifacts"]:
        assert DATA_SCIENTIST_SOURCE not in artifact.get("origin", [])


# 9. Boundary selection: owner in team.roles and artifact.subject == boundary.subject


def test_boundary_selection_rules():
    output = derive_context(FIXTURE_DIR)
    context = output["derived"]["contexts"][0]
    selected_contracts = context["selected_contracts"]
    assert len(selected_contracts) == 4
    assert "contract.cva.value_evidence.rvo" in selected_contracts
    assert "contract.fde.integration_path.rvo" in selected_contracts


# 10. Wrong-subject artifact exclusion


def test_wrong_subject_artifact_exclusion():
    bundle = load_bundle(FIXTURE_DIR)
    bad = copy.deepcopy(bundle)
    bad["artifacts"].append(
        {
            "id": "artifact.value_evidence.other",
            "type": "value_evidence",
            "label": "Other Value Evidence",
            "origin": [CVA_SOURCE],
            "subject": "source.neara_cva_job_description",
            "status": "expected_missing",
        }
    )
    bad["contracts"].append(
        {
            "id": "contract.cva.value_evidence.other",
            "label": "CVA Value Evidence for Other",
            "owner": "role.neara_cva",
            "artifact": "artifact.value_evidence.other",
        }
    )

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
        bad["artifacts"][-1]["subject"] = "source.neara_cva_job_description"
        (tmp_path / "artifacts.yaml").write_text(
            yaml.dump({"artifacts": bad["artifacts"]})
        )
        (tmp_path / "contracts.yaml").write_text(
            yaml.dump({"contracts": bad["contracts"]})
        )

        output = derive_context(tmp_path)
        selected = output["derived"]["contexts"][0]["selected_contracts"]
        assert "contract.cva.value_evidence.other" not in selected


# 11. Missing subject blocks context


def test_missing_subject_blocks_context():
    state = derive_context_for_state(None, [])
    assert state["coordination"] == "blocked"
    assert state["reason"] == "missing_subject"

    state = derive_context_for_state({"id": "b", "subject": None}, [])
    assert state["coordination"] == "blocked"


# 12. Expected-missing artifacts produce unresolved coordination


def test_expected_missing_artifacts_unresolved():
    output = derive_context(FIXTURE_DIR)
    state = output["derived"]["context_state"]
    assert state["coordination"] == "unresolved"
    assert state["reason"] == "missing_or_rejected_artifacts"


# 13. Present/validated artifacts produce ready coordination


@pytest.mark.parametrize(
    "statuses,expected,reason",
    [
        (["present", "present", "present", "present"], "ready", "selected_artifacts_satisfied"),
        (["validated", "validated", "validated", "validated"], "ready", "selected_artifacts_satisfied"),
        (["present", "validated", "present", "validated"], "ready", "selected_artifacts_satisfied"),
        (["expected_missing", "present"], "unresolved", "missing_or_rejected_artifacts"),
        (["rejected"], "unresolved", "missing_or_rejected_artifacts"),
        ([], "unresolved", "no_selected_artifacts"),
    ],
)
def test_artifact_status_coordination(statuses, expected, reason):
    boundary = {
        "id": "b",
        "subject": RVO_SOURCE,
        "team": "team.neara_account_team",
    }
    artifacts = [{"id": f"a{i}", "status": s} for i, s in enumerate(statuses)]
    state = derive_context_for_state(boundary, artifacts)
    assert state["coordination"] == expected
    assert state["reason"] == reason


def test_present_validated_fixture_ready_when_all_satisfied():
    bundle = load_bundle(FIXTURE_DIR)
    boundary = bundle["boundaries"][0]
    artifacts = [{**a, "status": "present"} for a in bundle["artifacts"]]
    state = derive_context_for_state(boundary, artifacts)
    assert state["coordination"] == "ready"
    assert state["reason"] == "selected_artifacts_satisfied"


# 14. Moment atom stays tiny


def test_moment_atom_stays_tiny():
    bundle = load_bundle(FIXTURE_DIR)
    for moment in bundle["moments"]:
        assert set(moment.keys()) == MOMENT_FIELDS


# 15. Deterministic output hashes


def test_deterministic_output_hashes():
    output_a = derive_context(FIXTURE_DIR)
    output_b = derive_context(FIXTURE_DIR)
    assert output_a["hashes"]["content"] == output_b["hashes"]["content"]
    assert output_a["trace"]["hash"] == output_b["trace"]["hash"]
    assert output_a["hashes"]["declared"] == output_b["hashes"]["declared"]
    assert output_a["hashes"]["derived"] == output_b["hashes"]["derived"]


def test_derive_output_shape():
    output = derive_context(FIXTURE_DIR)
    assert "answer" in output
    assert "declared" in output
    assert "derived" in output
    assert "trace" in output
    assert "hashes" in output

    for key in (
        "sources",
        "artifacts",
        "contracts",
        "roles",
        "teams",
        "profiles",
        "boundaries",
        "moments",
        "timpos",
    ):
        assert key in output["declared"]

    for key in ("role_views", "team_views", "contexts", "context_state"):
        assert key in output["derived"]


def test_derive_answer_generated_from_context():
    output = derive_context(FIXTURE_DIR)
    assert "is the subject of the" in output["answer"]
    assert "Neara RVO Account Context" in output["answer"]
    assert "unresolved" in output["answer"]
    assert "expected_missing" in output["answer"]


def test_trace_claims_generated_from_reducer_events():
    output = derive_context(FIXTURE_DIR)
    claims = output["trace"]["claims"]
    assert any("Boundary" in c and "selected" in c for c in claims)
    assert any("Eligible team roles" in c for c in claims)
    assert any("Contract" in c and "selected" in c for c in claims)
    assert any("status read: expected_missing" in c for c in claims)
    assert any("Context state resolved: unresolved" in c for c in claims)


def test_derive_contract_status_mapping():
    assert derive_contract_status("present") == "satisfied"
    assert derive_contract_status("validated") == "satisfied"
    assert derive_contract_status("expected_missing") == "unsatisfied"
    assert derive_contract_status("rejected") == "unsatisfied"


def test_validate_bundle_passes_for_fixture():
    bundle = load_bundle(FIXTURE_DIR)
    validate_bundle(bundle)


def test_team_excludes_data_scientist_role():
    bundle = load_bundle(FIXTURE_DIR)
    team = bundle["teams"][0]
    assert "role.neara_data_scientist" not in team["roles"]


def test_moments_attached_to_boundary_and_artifacts():
    output = derive_context(FIXTURE_DIR)
    moment_ids = output["derived"]["contexts"][0]["moments"]
    assert "moment.001" in moment_ids
    assert len(moment_ids) == 5
