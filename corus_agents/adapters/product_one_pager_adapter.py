"""Deterministic product one-pager adapter — minimal v0 implementation."""

from __future__ import annotations

import re
from typing import Any

EvidenceItem = dict[str, Any]

CAPABILITY_MARKERS = (
    "solution",
    "capability",
    "capabilities",
    "platform",
    "product",
    "use case",
    "use cases",
    "customer value",
    "benefits",
)

USE_CASE_PATTERN = re.compile(
    r"(?:use case[s]?|customer[s]? (?:can|use|benefit))",
    re.IGNORECASE,
)


def _evidence(
    text: str,
    source_id: str,
    *,
    section: str | None,
    signal_type: str,
) -> EvidenceItem:
    return {
        "text": text.strip(),
        "source_id": source_id,
        "page": None,
        "section": section,
        "signal_type": signal_type,
    }


def _first_line_title(text: str, filename: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    stem = filename.rsplit(".", 1)[0] if filename else ""
    return stem or None


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def adapt_product_one_pager(
    source_id: str,
    text: str,
    *,
    filename: str = "",
) -> dict[str, Any]:
    """
    Convert product one-pager text into a structured source packet.

    Does not infer artifacts, roles, or boundaries.
    """
    title = _first_line_title(text, filename)
    capabilities: list[EvidenceItem] = []
    use_cases: list[EvidenceItem] = []
    evidence_spans: list[EvidenceItem] = []

    if title:
        evidence_spans.append(_evidence(title, source_id, section="preamble", signal_type="title"))

    for sentence in _sentences(text):
        lowered = sentence.lower()
        if any(marker in lowered for marker in CAPABILITY_MARKERS):
            item = _evidence(sentence, source_id, section="body", signal_type="capability")
            capabilities.append(item)
            evidence_spans.append(item)
        if USE_CASE_PATTERN.search(sentence):
            item = _evidence(sentence, source_id, section="body", signal_type="use_case")
            use_cases.append(item)
            evidence_spans.append(item)

    return {
        "source_id": source_id,
        "document_type": "product_one_pager",
        "title": title,
        "sections": {"body": text.strip()},
        "signals": {
            "capabilities": capabilities,
            "use_cases": use_cases,
        },
        "evidence_spans": evidence_spans,
    }
