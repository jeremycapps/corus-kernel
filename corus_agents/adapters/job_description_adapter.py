"""Deterministic job description adapter — no LLM, no artifact inference."""

from __future__ import annotations

import re
from typing import Any

from corus_agents import interpretation_signals as signals

EvidenceItem = dict[str, Any]

SECTION_HEADER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("what_you_will_do", re.compile(
        r"^(?:what you will do|what you'll do|responsibilities|the role)\b",
        re.IGNORECASE,
    )),
    ("who_you_are", re.compile(
        r"^(?:who you are|requirements|qualifications|about you)\b",
        re.IGNORECASE,
    )),
    ("compensation", re.compile(
        r"^(?:compensation|salary|pay range|pay)\b",
        re.IGNORECASE,
    )),
    ("location", re.compile(
        r"^(?:location|where you(?:'ll| will) work)\b",
        re.IGNORECASE,
    )),
    ("benefits", re.compile(r"^(?:benefits|perks)\b", re.IGNORECASE)),
    ("employment_type", re.compile(
        r"^(?:employment type|employment)\b",
        re.IGNORECASE,
    )),
    ("department", re.compile(r"^(?:department|team)\b", re.IGNORECASE)),
    ("apply", re.compile(r"^(?:apply for this job|how to apply)\b", re.IGNORECASE)),
)

TOOL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("sdk", re.compile(r"\bsdk\b", re.IGNORECASE)),
    ("api", re.compile(r"\bapi\b", re.IGNORECASE)),
    ("python", re.compile(r"\bpython\b", re.IGNORECASE)),
    ("sql", re.compile(r"\bsql\b", re.IGNORECASE)),
    ("gis", re.compile(r"\bgis\b", re.IGNORECASE)),
    ("lidar", re.compile(r"\blidar\b", re.IGNORECASE)),
)

NEGATIVE_SECTIONS = frozenset({"compensation", "location", "benefits", "who_you_are"})


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _evidence(
    text: str,
    source_id: str,
    *,
    section: str | None,
    signal_type: str,
    page: int | None = None,
) -> EvidenceItem:
    return {
        "text": text.strip(),
        "source_id": source_id,
        "page": page,
        "section": section,
        "signal_type": signal_type,
    }


def split_sections(text: str) -> dict[str, str]:
    """Split job description text into named sections."""
    sections: dict[str, list[str]] = {"preamble": []}
    current = "preamble"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched_header = False
        header_candidate = line.split(":", 1)[0].strip()
        for section_name, pattern in SECTION_HEADER_PATTERNS:
            if pattern.match(header_candidate):
                current = section_name
                sections.setdefault(current, [])
                if ":" in line:
                    remainder = line.split(":", 1)[1].strip()
                    if remainder:
                        sections[current].append(remainder)
                matched_header = True
                break

        if not matched_header:
            sections.setdefault(current, []).append(line)

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if lines
    }


def extract_title(text: str, filename: str) -> str | None:
    """Extract job title from preamble or filename."""
    sections = split_sections(text)
    preamble = sections.get("preamble", "")
    lines = [line.strip() for line in preamble.splitlines() if line.strip()]
    if lines:
        candidate = lines[0].rstrip(":")
        if len(candidate) <= 120 and not _is_section_header(candidate):
            return candidate

    stem = filename.rsplit(".", 1)[0] if filename else ""
    if " @ " in stem:
        return stem.split(" @ ", 1)[0].strip()
    if " - " in stem:
        return stem.split(" - ", 1)[0].strip()
    return stem or None


def extract_company(text: str, filename: str) -> str | None:
    """Extract company name when obvious from preamble or filename."""
    sections = split_sections(text)
    preamble_lines = [
        line.strip()
        for line in sections.get("preamble", "").splitlines()
        if line.strip()
    ]
    if len(preamble_lines) >= 2:
        second = preamble_lines[1]
        if len(second) <= 80 and not _is_section_header(second):
            return second

    stem = filename.rsplit(".", 1)[0] if filename else ""
    if " @ " in stem:
        return stem.rsplit(" @ ", 1)[-1].strip()
    return None


def _is_section_header(line: str) -> bool:
    header_candidate = line.split(":", 1)[0].strip()
    return any(pattern.match(header_candidate) for _, pattern in SECTION_HEADER_PATTERNS)


def _lines_from_section(sections: dict[str, str], *names: str) -> list[str]:
    items: list[str] = []
    for name in names:
        block = sections.get(name, "")
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            cleaned = re.sub(r"^[-*•]\s+", "", stripped)
            items.append(cleaned)
    return items


def _match_phrases_in_text(
    text: str,
    phrases: tuple[str, ...] | frozenset[str],
    source_id: str,
    *,
    section: str | None,
    signal_type: str,
) -> list[EvidenceItem]:
    normalized = _normalize(text)
    found: list[EvidenceItem] = []
    for phrase in sorted(phrases, key=len, reverse=True):
        if phrase.lower() in normalized:
            found.append(_evidence(
                phrase,
                source_id,
                section=section,
                signal_type=signal_type,
            ))
    return found


def _sentences_with_phrases(
    lines: list[str],
    phrases: tuple[str, ...] | frozenset[str],
    source_id: str,
    *,
    section: str | None,
    signal_type: str,
) -> list[EvidenceItem]:
    found: list[EvidenceItem] = []
    for line in lines:
        normalized = _normalize(line)
        for phrase in sorted(phrases, key=len, reverse=True):
            if phrase.lower() in normalized:
                found.append(_evidence(line, source_id, section=section, signal_type=signal_type))
                break
    return found


def extract_responsibilities(
    sections: dict[str, str],
    source_id: str,
) -> list[EvidenceItem]:
    lines = _lines_from_section(sections, "what_you_will_do")
    if not lines:
        preamble_lines = _lines_from_section(sections, "preamble")
        lines = [
            line for line in preamble_lines
            if any(verb in _normalize(line) for verb in signals.ACTION_VERBS)
        ]
    return [
        _evidence(line, source_id, section="what_you_will_do", signal_type="responsibility")
        for line in lines
    ]


def extract_expected_outputs(
    sections: dict[str, str],
    source_id: str,
) -> list[EvidenceItem]:
    blocks = [
        sections.get("what_you_will_do", ""),
        sections.get("preamble", ""),
    ]
    found: list[EvidenceItem] = []
    for block in blocks:
        found.extend(_sentences_with_phrases(
            _lines_from_section({"block": block}, "block"),
            signals.OUTPUT_NOUNS,
            source_id,
            section="what_you_will_do" if block == sections.get("what_you_will_do") else "preamble",
            signal_type="expected_output",
        ))
    return found


def extract_accountabilities(
    sections: dict[str, str],
    source_id: str,
) -> list[EvidenceItem]:
    blocks = [
        sections.get("what_you_will_do", ""),
        sections.get("preamble", ""),
    ]
    found: list[EvidenceItem] = []
    for block in blocks:
        found.extend(_sentences_with_phrases(
            _lines_from_section({"block": block}, "block"),
            signals.ACCOUNTABILITY_LANGUAGE,
            source_id,
            section="what_you_will_do" if block == sections.get("what_you_will_do") else "preamble",
            signal_type="accountability",
        ))
    return found


def extract_stakeholder_groups(
    sections: dict[str, str],
    source_id: str,
) -> list[EvidenceItem]:
    haystack = "\n".join(sections.values())
    return _match_phrases_in_text(
        haystack,
        signals.STAKEHOLDER_LANGUAGE,
        source_id,
        section=None,
        signal_type="stakeholder",
    )


def extract_tools_or_systems(text: str, source_id: str) -> list[EvidenceItem]:
    found: list[EvidenceItem] = []
    for tool_name, pattern in TOOL_PATTERNS:
        if pattern.search(text):
            found.append(_evidence(
                tool_name.upper() if len(tool_name) <= 4 else tool_name.title(),
                source_id,
                section=None,
                signal_type="tool_or_system",
            ))
    return found


def extract_negative_sections(
    sections: dict[str, str],
    source_id: str,
) -> list[EvidenceItem]:
    found: list[EvidenceItem] = []
    for section_name in NEGATIVE_SECTIONS:
        block = sections.get(section_name, "")
        if not block:
            continue
        for line in _lines_from_section({section_name: block}, section_name):
            found.append(_evidence(
                line,
                source_id,
                section=section_name,
                signal_type="negative_section",
            ))

    haystack = "\n".join(sections.values())
    for phrase in signals.NEGATIVE_FILTERS:
        if phrase.lower() in _normalize(haystack):
            found.append(_evidence(
                phrase,
                source_id,
                section=None,
                signal_type="negative_filter",
            ))
    return found


def _field_from_section(
    sections: dict[str, str],
    section_name: str,
    source_id: str,
    signal_type: str,
) -> EvidenceItem | None:
    block = sections.get(section_name, "").strip()
    if not block:
        return None
    first_line = block.splitlines()[0].strip()
    return _evidence(first_line, source_id, section=section_name, signal_type=signal_type)


def adapt_job_description(
    source_id: str,
    text: str,
    *,
    filename: str = "",
) -> dict[str, Any]:
    """
    Convert job description text into a structured source packet.

    Does not infer artifacts, roles, or boundaries.
    """
    sections = split_sections(text)
    title = extract_title(text, filename)
    company = extract_company(text, filename)

    responsibilities = extract_responsibilities(sections, source_id)
    expected_outputs = extract_expected_outputs(sections, source_id)
    accountabilities = extract_accountabilities(sections, source_id)
    stakeholders = extract_stakeholder_groups(sections, source_id)
    tools = extract_tools_or_systems(text, source_id)
    negative_items = extract_negative_sections(sections, source_id)

    location = _field_from_section(sections, "location", source_id, "location")
    employment_type = _field_from_section(
        sections, "employment_type", source_id, "employment_type"
    )
    compensation = _field_from_section(sections, "compensation", source_id, "compensation")
    department = _field_from_section(sections, "department", source_id, "department")

    evidence_spans: list[EvidenceItem] = []
    if title:
        evidence_spans.append(_evidence(title, source_id, section="preamble", signal_type="title"))
    if company:
        evidence_spans.append(_evidence(company, source_id, section="preamble", signal_type="company"))
    for item in (
        responsibilities,
        expected_outputs,
        accountabilities,
        stakeholders,
        tools,
        negative_items,
    ):
        evidence_spans.extend(item)
    for item in (location, employment_type, compensation, department):
        if item:
            evidence_spans.append(item)

    negative_filters = [
        item for item in negative_items if item["signal_type"] == "negative_filter"
    ]

    return {
        "source_id": source_id,
        "document_type": "job_description",
        "title": title,
        "company": company,
        "department": department["text"] if department else None,
        "location": location["text"] if location else None,
        "employment_type": employment_type["text"] if employment_type else None,
        "compensation": compensation["text"] if compensation else None,
        "sections": sections,
        "signals": {
            "responsibilities": responsibilities,
            "expected_outputs": expected_outputs,
            "accountabilities": accountabilities,
            "stakeholders": stakeholders,
            "tools_or_systems": tools,
            "negative_filters": negative_filters,
        },
        "negative_sections": [
            item for item in negative_items if item["signal_type"] == "negative_section"
        ],
        "evidence_spans": evidence_spans,
    }
