"""Hardening tests for Corus Kernel v0 trust and determinism."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml

from corus_kernel.derive import derive_context
from corus_kernel.interpret import interpret_sources
from corus_kernel.loader import (
    DERIVE_BUNDLE_FILES,
    INTERPRET_CANDIDATE_FILES,
    load_bundle,
    load_sources,
)
from corus_kernel.schemas import ALLOWED_FIELDS
from corus_kernel.validate import validate_minimalism

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"
GOLDEN_PATH = FIXTURE_DIR / "golden" / "derive.json"
GITIGNORE_PATH = Path(__file__).parent.parent / ".gitignore"

RVO_SOURCE = "source.neara_rvo"
CVA_SOURCE = "source.neara_cva_job_description"
FDE_SOURCE = "source.neara_fde_job_description"
DIRECTOR_SOURCE = "source.neara_director_customer_implementation_job_description"
DATA_SCIENTIST_SOURCE = "source.neara_data_scientist_job_description"

JOB_DESCRIPTION_SOURCES = {CVA_SOURCE, FDE_SOURCE, DIRECTOR_SOURCE, DATA_SCIENTIST_SOURCE}


def _canonical_json(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


# 1. Candidate files generated but gitignored


def test_candidate_files_listed_in_gitignore():
    gitignore = GITIGNORE_PATH.read_text()
    for name in INTERPRET_CANDIDATE_FILES:
        assert name in gitignore


def test_derive_bundle_files_exclude_candidates():
    for filename in DERIVE_BUNDLE_FILES.values():
        assert "candidate" not in filename


# 2–3. derive uses admitted artifacts/contracts only, never *.candidate.yaml


def test_derive_reads_only_admitted_artifact_and_contract_files():
    assert DERIVE_BUNDLE_FILES["artifacts"] == "artifacts.yaml"
    assert DERIVE_BUNDLE_FILES["contracts"] == "contracts.yaml"
    assert "artifacts.candidate.yaml" not in DERIVE_BUNDLE_FILES.values()
    assert "contracts.candidate.yaml" not in DERIVE_BUNDLE_FILES.values()


def test_derive_ignores_candidate_files_when_both_exist():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in (
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
        admitted["artifacts"][0]["status"] = "present"
        (tmp_path / "artifacts.yaml").write_text(yaml.dump(admitted))
        (tmp_path / "contracts.yaml").write_text(
            (FIXTURE_DIR / "contracts.yaml").read_text()
        )

        candidate = yaml.safe_load((FIXTURE_DIR / "artifacts.yaml").read_text())
        for artifact in candidate["artifacts"]:
            artifact["status"] = "validated"
        (tmp_path / "artifacts.candidate.yaml").write_text(yaml.dump(candidate))

        bundle = load_bundle(tmp_path)
        assert bundle["artifacts"][0]["status"] == "present"


# 4. Source files remain raw sources only


def test_sources_are_declarations_not_parsed_content():
    sources = load_sources(FIXTURE_DIR)
    allowed = ALLOWED_FIELDS["source"]
    for source in sources:
        assert set(source.keys()) == allowed
        assert source["type"] == "document"
        assert source["locator"].startswith("sources/raw/")
        assert source["locator"].endswith(".pdf")


# 5. RVO never artifact.origin for CVA/FDE artifacts


def test_rvo_never_artifact_origin():
    bundle = load_bundle(FIXTURE_DIR)
    for artifact in bundle["artifacts"]:
        assert RVO_SOURCE not in artifact.get("origin", [])


# 6. CVA/FDE job descriptions never boundary.subject


def test_job_descriptions_never_boundary_subject():
    bundle = load_bundle(FIXTURE_DIR)
    for boundary in bundle["boundaries"]:
        assert boundary["subject"] not in JOB_DESCRIPTION_SOURCES
        assert boundary["subject"] == RVO_SOURCE


# 7. Data Scientist loaded but excluded from v0 boundary


def test_data_scientist_excluded_from_boundary_team():
    bundle = load_bundle(FIXTURE_DIR)
    team_roles = set(bundle["teams"][0]["roles"])
    assert "role.neara_data_scientist" not in team_roles

    output = derive_context(FIXTURE_DIR)
    owners = {
        c["owner"] for c in output["derived"]["contract_statuses"]
    }
    assert "role.neara_data_scientist" not in owners


# 8. Role / team / profile separation


def test_role_team_profile_separation():
    bundle = load_bundle(FIXTURE_DIR)

    for contract in bundle["contracts"]:
        assert "owner" in contract
        assert contract["owner"].startswith("role.")

    for team in bundle["teams"]:
        for role_id in team["roles"]:
            assert role_id.startswith("role.")

    for moment in bundle["moments"]:
        assert moment["actor"].startswith("profile.")

    boundary = bundle["boundaries"][0]
    assert boundary["orchestrator"].startswith("profile.")
    assert boundary["team"].startswith("team.")


# 9. Boundary contains only allowed fields


def test_boundary_minimal_fields():
    allowed = ALLOWED_FIELDS["boundary"]
    bundle = load_bundle(FIXTURE_DIR)
    for boundary in bundle["boundaries"]:
        assert set(boundary.keys()) == allowed


# 10. Moment contains only allowed fields


def test_moment_minimal_fields():
    allowed = ALLOWED_FIELDS["moment"]
    bundle = load_bundle(FIXTURE_DIR)
    for moment in bundle["moments"]:
        assert set(moment.keys()) == allowed


# Golden derive output


def test_derive_matches_golden_output():
    output = derive_context(FIXTURE_DIR)
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert output == golden


def test_golden_file_matches_canonical_serialization():
    output = derive_context(FIXTURE_DIR)
    assert _canonical_json(output) == GOLDEN_PATH.read_text(encoding="utf-8")


# Interpretation trace assertions


def _trace_steps_by_artifact(trace: list[dict], artifact_id: str) -> list[dict]:
    return [
        s
        for s in trace
        if s.get("artifact_id") == artifact_id and s.get("action") == "derive_artifact"
    ]


def test_interpretation_trace_artifact_provenance():
    result = interpret_sources(FIXTURE_DIR)
    trace = result["trace"]

    expectations = {
        "artifact.value_evidence.rvo": (CVA_SOURCE, RVO_SOURCE),
        "artifact.roi_case.rvo": (CVA_SOURCE, RVO_SOURCE),
        "artifact.technical_evidence.rvo": (FDE_SOURCE, RVO_SOURCE),
        "artifact.integration_path.rvo": (FDE_SOURCE, RVO_SOURCE),
    }
    for artifact_id, (origin, subject) in expectations.items():
        steps = _trace_steps_by_artifact(trace, artifact_id)
        assert len(steps) == 1, artifact_id
        step = steps[0]
        assert step["action"] == "derive_artifact"
        assert step["origin"] == origin
        assert step["subject"] == subject
        assert origin in step["detail"]
        assert subject in step["detail"]


def test_interpretation_trace_director_orchestrator():
    result = interpret_sources(FIXTURE_DIR)
    director_steps = [
        s
        for s in result["trace"]
        if s.get("source_id") == DIRECTOR_SOURCE
        and s.get("role") == "orchestrator_basis"
    ]
    assert len(director_steps) == 1
    assert "orchestrator" in director_steps[0]["detail"].lower()


def test_interpretation_trace_data_scientist_excluded():
    result = interpret_sources(FIXTURE_DIR)
    exclude_steps = [
        s for s in result["trace"] if s.get("action") == "exclude_source"
    ]
    assert len(exclude_steps) == 1
    step = exclude_steps[0]
    assert step["source_id"] == DATA_SCIENTIST_SOURCE
    assert "excluded" in step["detail"].lower()
    assert step["reason"] == "role_not_on_team"


def test_fixture_passes_minimalism_validation():
    validate_minimalism(load_bundle(FIXTURE_DIR))
