"""Tests for typed source preprocessing before LLM interpretation."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_agents import admission_agent, derive_agent, interpreter_agent, runner
from corus_agents.adapters.job_description_adapter import adapt_job_description
from corus_agents.source_inventory_agent import inventory_raw_sources, run as inventory_run
from corus_agents.source_preprocessor import (
    classify_document_type,
    preprocess,
    preprocess_source,
)

FIXTURE_V0 = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_v0"
FIXTURE_SMOKE = Path(__file__).parent / "fixtures" / "neara_rvo_boundary_smoke"

SAMPLE_JD = """
Customer Value Architect
Acme Corp

Department: Customer Success
Location: New York, NY (Hybrid)
Employment Type: Full-time
Compensation: Competitive salary and benefits

What you will do
- Drive adoption and value definition with customers
- Collaborate with customers to define business cases and ROI metrics
- Deliver value delivery reviews with business stakeholders

Who you are
- Strong communication skills

Apply for this job
""".strip()

SAMPLE_ONE_PAGER = """
Neara Risk and Value Optimization platform delivers solution capabilities and customer value.
Use cases include asset-level intelligence and intervention scenarios for electric networks.
""".strip()

UNKNOWN_TEXT = "Internal memo about quarterly planning priorities and staffing notes."

PREPROCESSING_MODULES = (
    Path(__file__).parent.parent / "corus_agents" / "source_preprocessor.py",
    Path(__file__).parent.parent / "corus_agents" / "source_inventory_agent.py",
    Path(__file__).parent.parent / "corus_agents" / "adapters" / "job_description_adapter.py",
    Path(__file__).parent.parent / "corus_agents" / "adapters" / "product_one_pager_adapter.py",
)


@pytest.fixture
def sample_source_id() -> str:
    return "source.customer_value_architect_acme"


def test_job_description_adapter_identifies_job_description(sample_source_id: str):
    packet = adapt_job_description(
        sample_source_id,
        SAMPLE_JD,
        filename="Customer Value Architect @ Acme.pdf",
    )
    assert packet["document_type"] == "job_description"
    assert classify_document_type(SAMPLE_JD, "job.pdf") == "job_description"


def test_job_description_adapter_extracts_title(sample_source_id: str):
    packet = adapt_job_description(
        sample_source_id,
        SAMPLE_JD,
        filename="Customer Value Architect @ Acme.pdf",
    )
    assert packet["title"] == "Customer Value Architect"


def test_job_description_adapter_extracts_responsibilities(sample_source_id: str):
    packet = adapt_job_description(
        sample_source_id,
        SAMPLE_JD,
        filename="Customer Value Architect @ Acme.pdf",
    )
    texts = [item["text"] for item in packet["signals"]["responsibilities"]]
    assert any("Drive adoption" in text for text in texts)
    assert any("business cases" in text for text in texts)


def test_job_description_adapter_extracts_expected_outputs(sample_source_id: str):
    packet = adapt_job_description(
        sample_source_id,
        SAMPLE_JD,
        filename="Customer Value Architect @ Acme.pdf",
    )
    texts = [item["text"] for item in packet["signals"]["expected_outputs"]]
    assert any("business cases" in text.lower() for text in texts)
    assert any("roi metrics" in text.lower() for text in texts)


def test_job_description_adapter_extracts_stakeholder_groups(sample_source_id: str):
    packet = adapt_job_description(
        sample_source_id,
        SAMPLE_JD,
        filename="Customer Value Architect @ Acme.pdf",
    )
    texts = [item["text"].lower() for item in packet["signals"]["stakeholders"]]
    assert "business stakeholders" in texts or any("stakeholder" in text for text in texts)


def test_job_description_adapter_applies_negative_filters(sample_source_id: str):
    packet = adapt_job_description(
        sample_source_id,
        SAMPLE_JD,
        filename="Customer Value Architect @ Acme.pdf",
    )
    negative_texts = [
        item["text"].lower()
        for item in packet["signals"]["negative_filters"]
    ]
    negative_sections = [item["section"] for item in packet["negative_sections"]]
    assert any("competitive salary" in text or "salary" in text for text in negative_texts)
    assert "compensation" in negative_sections
    assert "location" in negative_sections


def test_source_packets_include_source_id_on_every_evidence_span(sample_source_id: str):
    packet = adapt_job_description(
        sample_source_id,
        SAMPLE_JD,
        filename="Customer Value Architect @ Acme.pdf",
    )
    assert packet["evidence_spans"]
    for span in packet["evidence_spans"]:
        assert span["source_id"] == sample_source_id
        assert span["text"]
        assert span["signal_type"]


def test_source_packets_do_not_contain_candidate_artifacts_or_contracts():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(FIXTURE_V0 / "sources", tmp_path / "sources")
        payload = preprocess(tmp_path)

    serialized = json.dumps(payload)
    assert "artifact." not in serialized
    assert "contract." not in serialized
    assert "candidate" not in serialized.lower()
    for packet in payload["source_packets"]:
        assert "artifacts" not in packet
        assert "contracts" not in packet


def test_product_one_pager_classified_separately_from_job_description():
    assert classify_document_type(SAMPLE_ONE_PAGER, "one-pager.pdf") == "product_one_pager"
    assert classify_document_type(SAMPLE_JD, "job.pdf") == "job_description"
    assert classify_document_type(SAMPLE_ONE_PAGER, "job.pdf") != "job_description"


def test_unknown_document_type_does_not_produce_role_or_artifact_candidates():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sources_dir = tmp_path / "sources"
        text_dir = sources_dir / "text"
        text_dir.mkdir(parents=True)
        (text_dir / "source.internal_memo.txt").write_text(UNKNOWN_TEXT, encoding="utf-8")
        (sources_dir / "sources.yaml").write_text(
            yaml.dump({
                "sources": [{
                    "id": "source.internal_memo",
                    "type": "document",
                    "label": "Memo",
                    "locator": "sources/raw/memo.txt",
                }]
            }),
            encoding="utf-8",
        )

        packet = preprocess_source(
            tmp_path,
            {
                "id": "source.internal_memo",
                "locator": "sources/raw/memo.txt",
                "type": "document",
                "label": "Memo",
            },
        )

    assert packet["document_type"] == "unknown"
    assert packet["signals"] == {}
    assert packet["evidence_spans"] == []


def test_unknown_classification_from_plain_text():
    assert classify_document_type(UNKNOWN_TEXT, "memo.txt") == "unknown"


def test_no_neara_specific_artifact_ids_in_preprocessing_code():
    forbidden = ("artifact.", "contract.", "role.neara", "source.neara")
    for path in PREPROCESSING_MODULES:
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{token} found in {path.name}"


def test_source_inventory_writes_generic_declarations_without_role_inference():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_dir = tmp_path / "sources" / "raw"
        raw_dir.mkdir(parents=True)
        (raw_dir / "Customer Value Architect @ Neara.pdf").touch()

        result = inventory_run(tmp_path)
        sources_path = Path(result.outputs["sources_yaml"])
        payload = yaml.safe_load(sources_path.read_text(encoding="utf-8"))

        assert len(payload["sources"]) == 1
        decl = payload["sources"][0]
        assert decl["id"].startswith("source.")
        assert decl["id"] == "source.customer_value_architect_neara"
        assert "role" not in decl
        assert "artifact" not in decl["id"]


def test_preprocess_writes_source_packets_json():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(FIXTURE_V0 / "sources", tmp_path / "sources")
        payload = preprocess(tmp_path)

        output_path = tmp_path / "source_packets.json"
        assert output_path.exists()
        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        assert loaded == payload
        assert len(payload["source_packets"]) == 5


def test_preprocess_classifies_fixture_sources():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(FIXTURE_V0 / "sources", tmp_path / "sources")
        payload = preprocess(tmp_path)

    by_id = {packet["source_id"]: packet for packet in payload["source_packets"]}
    assert by_id["source.neara_rvo"]["document_type"] == "product_one_pager"
    assert by_id["source.neara_cva_job_description"]["document_type"] == "job_description"
    assert by_id["source.neara_fde_job_description"]["document_type"] == "job_description"


def test_existing_derive_admission_workflow_unchanged():
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
            shutil.copy2(FIXTURE_SMOKE / name, tmp_path / name)
        shutil.copytree(FIXTURE_SMOKE / "sources", tmp_path / "sources", symlinks=True)

        preprocess(tmp_path)
        runner.main(["run", str(tmp_path)])
        admission_agent.run(tmp_path, approve=True)
        code = runner.main(["run", str(tmp_path)])

        assert code == 0
        assert (tmp_path / "derive.output.json").exists()
        assert (tmp_path / "source_packets.json").exists()


def test_interpreter_workflow_still_independent_of_preprocessing():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copy2(FIXTURE_V0 / "artifacts.yaml", tmp_path / "artifacts.yaml")
        shutil.copy2(FIXTURE_V0 / "contracts.yaml", tmp_path / "contracts.yaml")
        for name in (
            "roles.yaml",
            "teams.yaml",
            "profiles.yaml",
            "boundaries.yaml",
            "moments.yaml",
            "timpos.yaml",
        ):
            shutil.copy2(FIXTURE_V0 / name, tmp_path / name)
        shutil.copytree(FIXTURE_V0 / "sources", tmp_path / "sources")

        result = interpreter_agent.run(tmp_path)
        assert result.outputs["artifact_count"] == 4
        derive_agent.run(tmp_path)
