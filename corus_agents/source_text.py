"""PDF and text extraction for agent interpretation — not used by derive."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Filename heuristics for bootstrap when sources.yaml is absent.
FILENAME_SOURCE_HINTS: tuple[tuple[str, str, str], ...] = (
    ("one-pager - rvo", "source.neara_rvo", "Neara Risk and Value Optimization"),
    ("customer value architect", "source.neara_cva_job_description", "Neara Customer Value Architect Job Description"),
    ("forward deployed engineer", "source.neara_fde_job_description", "Neara Forward Deployed Engineer Job Description"),
    ("director", "source.neara_director_customer_implementation_job_description", "Neara Director Customer Implementation Job Description"),
    ("data scientist", "source.neara_data_scientist_job_description", "Neara Data Scientist Job Description"),
)


def extract_pdf_text(pdf_path: Path) -> tuple[str, str]:
    """
    Extract text from a PDF file.

    Returns (text, status) where status is ok, text_extraction_unavailable,
    or text_extraction_failed.
    """
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]
    except ImportError:
        return "", "text_extraction_unavailable"

    try:
        reader = PdfReader(str(pdf_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            return "", "text_extraction_failed"
        return text, "ok"
    except Exception:
        return "", "text_extraction_failed"


def text_stub_path(fixture_dir: Path, source_id: str, locator: str) -> Path:
    """Optional deterministic text stub for tests: sources/text/<source_id>.txt."""
    stub_by_id = fixture_dir / "sources" / "text" / f"{source_id}.txt"
    if stub_by_id.exists():
        return stub_by_id
    pdf_name = Path(locator).stem
    return fixture_dir / "sources" / "text" / f"{pdf_name}.txt"


def load_source_text(
    fixture_dir: Path,
    source_id: str,
    locator: str,
) -> tuple[str, str]:
    """
    Load interpretable text for a source.

    Prefers sources/text/*.txt stubs, then PDF extraction.
    """
    fixture_dir = Path(fixture_dir)
    stub = text_stub_path(fixture_dir, source_id, locator)
    if stub.exists():
        return stub.read_text(encoding="utf-8"), "text_stub"

    pdf_path = fixture_dir / locator
    if pdf_path.suffix.lower() == ".pdf" and pdf_path.exists():
        return extract_pdf_text(pdf_path)

    return "", "text_extraction_unavailable"


def infer_source_declaration(pdf_path: Path) -> dict[str, str] | None:
    """Infer a source declaration from a raw PDF filename."""
    name = pdf_path.name.lower()
    for hint, source_id, label in FILENAME_SOURCE_HINTS:
        if hint in name:
            return {
                "id": source_id,
                "type": "document",
                "label": label,
                "locator": f"sources/raw/{pdf_path.name}",
            }
    slug = re_slug(pdf_path.stem)
    return {
        "id": f"source.{slug}",
        "type": "document",
        "label": pdf_path.stem,
        "locator": f"sources/raw/{pdf_path.name}",
    }


def re_slug(text: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:64] or "document"


def bootstrap_sources_from_raw(fixture_dir: Path) -> list[dict[str, Any]]:
    """Build source declarations from sources/raw/*.pdf when sources.yaml is absent."""
    raw_dir = Path(fixture_dir) / "sources" / "raw"
    if not raw_dir.exists():
        return []
    sources: list[dict[str, Any]] = []
    for pdf in sorted(raw_dir.glob("*.pdf")):
        decl = infer_source_declaration(pdf)
        if decl:
            sources.append(decl)
    return sources


def load_or_bootstrap_sources(fixture_dir: Path) -> list[dict[str, Any]]:
    import yaml

    fixture_dir = Path(fixture_dir)
    sources_yaml = fixture_dir / "sources" / "sources.yaml"
    if sources_yaml.exists():
        data = yaml.safe_load(sources_yaml.read_text(encoding="utf-8")) or {}
        return list(data.get("sources", []))
    return bootstrap_sources_from_raw(fixture_dir)
