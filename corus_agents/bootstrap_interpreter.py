"""Agent bootstrap interpreter with phrase-level evidence traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from corus_agents import interpretation_signals as signals
from corus_agents.source_text import load_or_bootstrap_sources, load_source_text

RVO_SOURCE = "source.neara_rvo"
CVA_SOURCE = "source.neara_cva_job_description"
FDE_SOURCE = "source.neara_fde_job_description"
DIRECTOR_SOURCE = "source.neara_director_customer_implementation_job_description"
DATA_SCIENTIST_SOURCE = "source.neara_data_scientist_job_description"

ROLE_CVA = "role.neara_cva"
ROLE_FDE = "role.neara_fde"
ROLE_DIRECTOR = "role.neara_director_customer_implementation"
ROLE_DATA_SCIENTIST = "role.neara_data_scientist"
TEAM_NEARA = "team.neara_account_team"
PROFILE_DIRECTOR = "profile.neara_director_customer_implementation"
BOUNDARY_RVO = "boundary.neara.rvo.account_context"

V0_TEAM_ROLES = (
    ROLE_DIRECTOR,
    ROLE_CVA,
    ROLE_FDE,
)

CANDIDATE_FILES = {
    "roles": "roles.candidate.yaml",
    "teams": "teams.candidate.yaml",
    "profiles": "profiles.candidate.yaml",
    "boundaries": "boundaries.candidate.yaml",
    "moments": "moments.candidate.yaml",
    "timpos": "timpos.candidate.yaml",
    "artifacts": "artifacts.candidate.yaml",
    "contracts": "contracts.candidate.yaml",
}


def _trace_step(action: str, **fields: Any) -> dict[str, Any]:
    return {"action": action, **fields}


def _matched_from_phrases(text: str, phrase_set: frozenset[str]) -> list[str]:
    return signals.match_phrases(text, phrase_set)


def _classify_source(source_id: str, text: str, extraction_status: str) -> dict[str, Any]:
    if source_id == RVO_SOURCE:
        phrases = _matched_from_phrases(text, signals.RVO_BOUNDARY_PHRASES)
        return {
            "source_id": source_id,
            "relationship_role": "boundary_subject",
            "matched_phrases": phrases,
            "candidate_boundary_field": "subject",
            "extraction_status": extraction_status,
            "admission_required": True,
        }
    if source_id == DIRECTOR_SOURCE:
        phrases = _matched_from_phrases(text, signals.DIRECTOR_BOUNDARY_PHRASES)
        return {
            "source_id": source_id,
            "relationship_role": "orchestrator_basis",
            "supports_profile": PROFILE_DIRECTOR,
            "matched_phrases": phrases,
            "candidate_boundary_field": "orchestrator",
            "extraction_status": extraction_status,
            "admission_required": True,
        }
    if source_id == CVA_SOURCE:
        phrases = _matched_from_phrases(text, signals.CVA_ARTIFACT_PHRASES)
        return {
            "source_id": source_id,
            "relationship_role": "artifact_origin",
            "role": ROLE_CVA,
            "matched_phrases": phrases,
            "extraction_status": extraction_status,
            "admission_required": True,
        }
    if source_id == FDE_SOURCE:
        phrases = _matched_from_phrases(text, signals.FDE_ARTIFACT_PHRASES)
        return {
            "source_id": source_id,
            "relationship_role": "artifact_origin",
            "role": ROLE_FDE,
            "matched_phrases": phrases,
            "extraction_status": extraction_status,
            "admission_required": True,
        }
    if source_id == DATA_SCIENTIST_SOURCE:
        phrases = _matched_from_phrases(text, signals.DATA_SCIENTIST_FUTURE_PHRASES)
        return {
            "source_id": source_id,
            "relationship_role": "future_artifact_origin",
            "role": ROLE_DATA_SCIENTIST,
            "matched_phrases": phrases,
            "reason": "role_not_on_v0_team",
            "extraction_status": extraction_status,
            "admission_required": False,
        }
    return {
        "source_id": source_id,
        "relationship_role": "unknown",
        "extraction_status": extraction_status,
        "admission_required": False,
    }


def _artifact_trace(
    artifact: dict[str, Any],
    matched_phrases: list[str],
    signal_groups: list[str],
) -> dict[str, Any]:
    return _trace_step(
        "derive_artifact",
        artifact_id=artifact["id"],
        artifact_type=artifact["type"],
        origin=artifact["origin"][0],
        subject=artifact["subject"],
        detail=(
            f"{artifact['id']} from {artifact['origin'][0]} "
            f"with subject {artifact['subject']}"
        ),
        matched_phrases=matched_phrases,
        signal_groups=signal_groups,
        confidence=signals.artifact_inference_strength(
            signals.match_signals(" ".join(matched_phrases))
        ),
        admission_required=True,
    )


def _derive_candidates(
    classifications: list[dict[str, Any]],
    source_texts: dict[str, str],
) -> tuple[list[dict], list[dict], list[dict]]:
    artifacts: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []

    cva_text = source_texts.get(CVA_SOURCE, "")
    fde_text = source_texts.get(FDE_SOURCE, "")

    cva_class = next((c for c in classifications if c["source_id"] == CVA_SOURCE), None)
    fde_class = next((c for c in classifications if c["source_id"] == FDE_SOURCE), None)

    if cva_class and signals.has_artifact_evidence(
        signals.match_signals(cva_text), signals.CVA_ARTIFACT_PHRASES, cva_text
    ):
        cva_phrases = cva_class.get("matched_phrases", [])
        cva_groups = signals.signal_groups_for_phrases(cva_phrases, cva_text)
        cva_specs = [
            ("artifact.value_evidence.rvo", "value_evidence", "RVO Value Evidence", "value_evidence"),
            ("artifact.roi_case.rvo", "roi_case", "RVO ROI Case", "roi_case"),
        ]
        for aid, atype, label, ctype in cva_specs:
            artifact = {
                "id": aid,
                "type": atype,
                "label": label,
                "origin": [CVA_SOURCE],
                "subject": RVO_SOURCE,
                "status": "expected_missing",
            }
            artifacts.append(artifact)
            trace.append(_artifact_trace(artifact, cva_phrases, cva_groups))
            contract_labels = {
                "value_evidence": "CVA Value Evidence for RVO",
                "roi_case": "CVA ROI Case for RVO",
            }
            contracts.append({
                "id": f"contract.cva.{ctype}.rvo",
                "label": contract_labels[ctype],
                "owner": ROLE_CVA,
                "artifact": aid,
            })
            trace.append(_trace_step(
                "derive_contract",
                contract_id=f"contract.cva.{ctype}.rvo",
                artifact_id=aid,
                owner=ROLE_CVA,
                admission_required=True,
            ))

    if fde_class and signals.has_artifact_evidence(
        signals.match_signals(fde_text), signals.FDE_ARTIFACT_PHRASES, fde_text
    ):
        fde_phrases = fde_class.get("matched_phrases", [])
        fde_groups = signals.signal_groups_for_phrases(fde_phrases, fde_text)
        fde_specs = [
            ("artifact.technical_evidence.rvo", "technical_evidence", "RVO Technical Evidence", "technical_evidence"),
            ("artifact.integration_path.rvo", "integration_path", "RVO Integration Path", "integration_path"),
        ]
        for aid, atype, label, ctype in fde_specs:
            artifact = {
                "id": aid,
                "type": atype,
                "label": label,
                "origin": [FDE_SOURCE],
                "subject": RVO_SOURCE,
                "status": "expected_missing",
            }
            artifacts.append(artifact)
            trace.append(_artifact_trace(artifact, fde_phrases, fde_groups))
            contracts.append({
                "id": f"contract.fde.{ctype}.rvo",
                "label": (
                    "FDE Technical Evidence for RVO"
                    if ctype == "technical_evidence"
                    else "FDE Integration Path for RVO"
                ),
                "owner": ROLE_FDE,
                "artifact": aid,
            })
            trace.append(_trace_step(
                "derive_contract",
                contract_id=f"contract.fde.{ctype}.rvo",
                artifact_id=aid,
                owner=ROLE_FDE,
                admission_required=True,
            ))

    return artifacts, contracts, trace


def _context_candidates() -> dict[str, list[dict[str, Any]]]:
    """Deterministic Neara v0 context candidates inferred from source set."""
    return {
        "roles": [
            {"id": ROLE_DIRECTOR, "label": "Director, Customer Implementation"},
            {"id": ROLE_CVA, "label": "Customer Value Architect"},
            {"id": ROLE_FDE, "label": "Forward Deployed Engineer"},
            {"id": ROLE_DATA_SCIENTIST, "label": "Data Scientist"},
        ],
        "teams": [{
            "id": TEAM_NEARA,
            "label": "Neara Account Team",
            "roles": list(V0_TEAM_ROLES),
        }],
        "profiles": [
            {"id": PROFILE_DIRECTOR, "type": "role", "ref": ROLE_DIRECTOR},
            {"id": "profile.neara_cva", "type": "role", "ref": ROLE_CVA},
            {"id": "profile.neara_fde", "type": "role", "ref": ROLE_FDE},
            {"id": "profile.corus_resolver", "type": "system", "ref": "system.corus"},
        ],
        "boundaries": [{
            "id": BOUNDARY_RVO,
            "label": "Neara RVO Account Context",
            "orchestrator": PROFILE_DIRECTOR,
            "team": TEAM_NEARA,
            "subject": RVO_SOURCE,
        }],
        "moments": [
            {
                "id": "moment.001",
                "timpo": "timpo.0001",
                "actor": PROFILE_DIRECTOR,
                "via": "orchestrate.account_context",
                "object": RVO_SOURCE,
                "previous": None,
            },
        ],
        "timpos": [{"id": "timpo.0001", "t": 1, "p": 1}],
    }


def bootstrap(fixture_dir: Path, *, write_sources_yaml: bool = False) -> dict[str, Any]:
    """
    Bootstrap candidate objects and interpretation trace from source files.

    Never writes admitted YAML.
    """
    fixture_dir = Path(fixture_dir)
    sources = load_or_bootstrap_sources(fixture_dir)

    if write_sources_yaml or not (fixture_dir / "sources" / "sources.yaml").exists():
        sources_path = fixture_dir / "sources" / "sources.yaml"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        with sources_path.open("w", encoding="utf-8") as handle:
            yaml.dump({"sources": sources}, handle, default_flow_style=False, sort_keys=False)

    trace: list[dict[str, Any]] = []
    source_texts: dict[str, str] = {}
    source_signal_reports: list[dict[str, Any]] = []
    classifications: list[dict[str, Any]] = []
    excluded_sources: list[dict[str, Any]] = []
    negative_filters_all: list[dict[str, Any]] = []

    known_ids = {s["id"] for s in sources}

    for source in sources:
        text, status = load_source_text(fixture_dir, source["id"], source["locator"])
        source_texts[source["id"]] = text
        signal_report = signals.build_source_signal_report(source["id"], text, status)
        source_signal_reports.append(signal_report)
        if signal_report["negative_filters_applied"]:
            negative_filters_all.append({
                "source_id": source["id"],
                "phrases": signal_report["negative_filters_applied"],
            })

        trace.append(_trace_step(
            "load_source",
            source_id=source["id"],
            detail=f"Loaded {source['id']}",
            extraction_status=status,
        ))

        classification = _classify_source(source["id"], text, status)
        classifications.append(classification)

        if classification["relationship_role"] == "boundary_subject":
            trace.append(_trace_step(
                "classify_source",
                source_id=source["id"],
                relationship_role="boundary_subject",
                matched_phrases=classification.get("matched_phrases", []),
                candidate_boundary_field="subject",
                admission_required=True,
                detail="RVO boundary subject intelligence, not artifact origin",
            ))
        elif classification["relationship_role"] == "orchestrator_basis":
            trace.append(_trace_step(
                "classify_source",
                source_id=source["id"],
                relationship_role="orchestrator_basis",
                supports_profile=classification.get("supports_profile"),
                matched_phrases=classification.get("matched_phrases", []),
                candidate_boundary_field="orchestrator",
                admission_required=True,
                detail=f"{source['id']} supports orchestrator role",
            ))
        elif classification["relationship_role"] == "future_artifact_origin":
            excluded_sources.append(classification)
            trace.append(_trace_step(
                "exclude_source",
                source_id=source["id"],
                relationship_role="future_artifact_origin",
                matched_phrases=classification.get("matched_phrases", []),
                reason=classification.get("reason"),
                admission_required=False,
                detail=f"{source['id']} loaded but excluded from v0 boundary",
            ))
        elif classification["relationship_role"] == "artifact_origin":
            trace.append(_trace_step(
                "classify_source",
                source_id=source["id"],
                relationship_role="artifact_origin",
                role=classification.get("role"),
                matched_phrases=classification.get("matched_phrases", []),
                admission_required=True,
                detail=f"{source['id']} is artifact origin for {classification.get('role')}",
            ))

    artifacts, contracts, artifact_trace = _derive_candidates(classifications, source_texts)
    trace.extend(artifact_trace)

    context = _context_candidates()
    candidates = {
        **context,
        "artifacts": artifacts,
        "contracts": contracts,
    }

    for key, filename in CANDIDATE_FILES.items():
        path = fixture_dir / filename
        collection = key if key != "teams" else "teams"
        with path.open("w", encoding="utf-8") as handle:
            yaml.dump({collection: candidates[key]}, handle, default_flow_style=False, sort_keys=False)

    bootstrap_report = {
        "fixture_dir": str(fixture_dir),
        "source_files": [s["locator"] for s in sources],
        "source_declarations": sources,
        "source_classifications": classifications,
        "source_signal_reports": source_signal_reports,
        "candidate_roles": context["roles"],
        "candidate_team": context["teams"],
        "candidate_profiles": context["profiles"],
        "candidate_boundary": context["boundaries"],
        "candidate_artifacts": artifacts,
        "candidate_contracts": contracts,
        "excluded_sources": excluded_sources,
        "negative_filters_applied": negative_filters_all,
        "admission_required": bool(artifacts or contracts),
    }

    report_path = fixture_dir / "bootstrap_report.json"
    trace_path = fixture_dir / "interpretation_trace.json"
    report_path.write_text(json.dumps(bootstrap_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "artifacts": artifacts,
        "contracts": contracts,
        "trace": trace,
        "bootstrap_report": bootstrap_report,
        "sources": sources,
        "known_ids": known_ids,
    }
