"""Typed source preprocessing — deterministic packets for future LLM interpretation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from corus_agents.adapters.job_description_adapter import adapt_job_description
from corus_agents.adapters.product_one_pager_adapter import adapt_product_one_pager
from corus_agents.source_inventory_agent import load_sources
from corus_agents.source_text import load_source_text

SOURCE_PACKETS_FILE = "source_packets.json"

JOB_DESCRIPTION_MARKERS = (
    "employment type",
    "compensation",
    "location type",
    "what you will do",
    "who you are",
    "apply for this job",
    "full-time",
    "full time",
    "salary",
    "benefits",
    "hybrid",
    "remote",
    "responsibilities",
    "qualifications",
)

PRODUCT_ONE_PAGER_MARKERS = (
    "solution",
    "capability",
    "capabilities",
    "benefits",
    "use case",
    "use cases",
    "product",
    "platform",
    "customer value",
)


def classify_document_type(text: str, filename: str) -> str:
    """Classify a source document using deterministic filename/text heuristics."""
    haystack = f"{filename} {text}".lower()

    jd_score = sum(1 for marker in JOB_DESCRIPTION_MARKERS if marker in haystack)
    pop_score = sum(1 for marker in PRODUCT_ONE_PAGER_MARKERS if marker in haystack)

    if jd_score > pop_score and jd_score >= 2:
        return "job_description"
    if pop_score > jd_score and pop_score >= 2:
        return "product_one_pager"
    if jd_score >= 1 and any(
        marker in haystack for marker in ("apply for this job", "what you will do", "who you are")
    ):
        return "job_description"
    if pop_score >= 2 and jd_score == 0:
        return "product_one_pager"
    return "unknown"


def build_unknown_packet(source_id: str, text: str, filename: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "document_type": "unknown",
        "title": None,
        "sections": {},
        "signals": {},
        "evidence_spans": [],
        "extraction_status": "unclassified",
        "filename": filename,
        "text_length": len(text),
    }


def preprocess_source(
    fixture_dir: Path,
    source: dict[str, Any],
) -> dict[str, Any]:
    """Preprocess one source declaration into a typed source packet."""
    source_id = source["id"]
    locator = source["locator"]
    filename = Path(locator).name
    text, extraction_status = load_source_text(fixture_dir, source_id, locator)
    document_type = classify_document_type(text, filename)

    if document_type == "job_description":
        packet = adapt_job_description(source_id, text, filename=filename)
    elif document_type == "product_one_pager":
        packet = adapt_product_one_pager(source_id, text, filename=filename)
    else:
        packet = build_unknown_packet(source_id, text, filename)

    packet["extraction_status"] = extraction_status
    packet["filename"] = filename
    return packet


def preprocess(fixture_dir: Path) -> dict[str, Any]:
    """
    Load sources, classify document types, and write source_packets.json.

    Does not generate artifacts, contracts, or admitted YAML.
    """
    fixture_dir = Path(fixture_dir)
    sources = load_sources(fixture_dir)
    packets = [preprocess_source(fixture_dir, source) for source in sources]
    payload = {"source_packets": packets}

    output_path = fixture_dir / SOURCE_PACKETS_FILE
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def load_source_packets(fixture_dir: Path) -> dict[str, Any]:
    path = Path(fixture_dir) / SOURCE_PACKETS_FILE
    if not path.exists():
        return {"source_packets": []}
    return json.loads(path.read_text(encoding="utf-8"))
