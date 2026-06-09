"""Rule-based source interpretation producing candidate artifacts and contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from corus_kernel.loader import load_sources

# Source IDs used by interpretation rules.
RVO_SOURCE = "source.neara_rvo"
CVA_SOURCE = "source.neara_cva_job_description"
FDE_SOURCE = "source.neara_fde_job_description"
DIRECTOR_SOURCE = "source.neara_director_customer_implementation_job_description"
DATA_SCIENTIST_SOURCE = "source.neara_data_scientist_job_description"

ROLE_CVA = "role.neara_cva"
ROLE_FDE = "role.neara_fde"
ROLE_DIRECTOR = "role.neara_director_customer_implementation"
ROLE_DATA_SCIENTIST = "role.neara_data_scientist"


def _source_ids(sources: list[dict[str, Any]]) -> set[str]:
    return {s["id"] for s in sources}


def interpret_sources(fixture_dir: Path) -> dict[str, Any]:
    """
    Read sources and produce candidate artifacts, contracts, and trace.

    Sources do not become artifacts silently — this explicit step derives
    candidates from rule-based interpretation of each source's role.
    """
    fixture_dir = Path(fixture_dir)
    sources = load_sources(fixture_dir)
    known = _source_ids(sources)

    trace_steps: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []

    def step(action: str, detail: str, **extra: Any) -> None:
        trace_steps.append({"action": action, "detail": detail, **extra})

    for source in sources:
        step("load_source", f"Loaded {source['id']}", source_id=source["id"])

    # RVO is boundary subject, not artifact origin.
    if RVO_SOURCE in known:
        step(
            "classify_source",
            "RVO source is boundary subject intelligence, not artifact origin",
            source_id=RVO_SOURCE,
            role="boundary_subject",
        )

    # Director JD justifies orchestrator; no v0 artifacts.
    if DIRECTOR_SOURCE in known:
        step(
            "classify_source",
            "Director JD supports orchestrator role; no v0 artifacts derived",
            source_id=DIRECTOR_SOURCE,
            role="orchestrator_basis",
            supports_role=ROLE_DIRECTOR,
        )

    # CVA JD origin for value/adoption artifacts.
    if CVA_SOURCE in known and RVO_SOURCE in known:
        cva_artifacts = [
            {
                "id": "artifact.value_evidence.rvo",
                "type": "value_evidence",
                "label": "RVO Value Evidence",
                "origin": [CVA_SOURCE],
                "subject": RVO_SOURCE,
                "status": "expected_missing",
            },
            {
                "id": "artifact.roi_case.rvo",
                "type": "roi_case",
                "label": "RVO ROI Case",
                "origin": [CVA_SOURCE],
                "subject": RVO_SOURCE,
                "status": "expected_missing",
            },
        ]
        artifacts.extend(cva_artifacts)
        step(
            "derive_artifacts",
            "CVA JD origin for value_evidence and roi_case artifacts on RVO subject",
            source_id=CVA_SOURCE,
            artifact_ids=[a["id"] for a in cva_artifacts],
        )
        cva_contract_labels = {
            "value_evidence": "CVA Value Evidence for RVO",
            "roi_case": "CVA ROI Case for RVO",
        }
        for artifact in cva_artifacts:
            contracts.append(
                {
                    "id": f"contract.cva.{artifact['type']}.rvo",
                    "label": cva_contract_labels[artifact["type"]],
                    "owner": ROLE_CVA,
                    "artifact": artifact["id"],
                }
            )
        step(
            "derive_contracts",
            "CVA-owned contracts for value artifacts",
            owner=ROLE_CVA,
            contract_ids=[c["id"] for c in contracts if c["owner"] == ROLE_CVA],
        )

    # FDE JD origin for technical/implementation artifacts.
    if FDE_SOURCE in known and RVO_SOURCE in known:
        fde_artifacts = [
            {
                "id": "artifact.technical_evidence.rvo",
                "type": "technical_evidence",
                "label": "RVO Technical Evidence",
                "origin": [FDE_SOURCE],
                "subject": RVO_SOURCE,
                "status": "expected_missing",
            },
            {
                "id": "artifact.integration_path.rvo",
                "type": "integration_path",
                "label": "RVO Integration Path",
                "origin": [FDE_SOURCE],
                "subject": RVO_SOURCE,
                "status": "expected_missing",
            },
        ]
        artifacts.extend(fde_artifacts)
        step(
            "derive_artifacts",
            "FDE JD origin for technical_evidence and integration_path artifacts on RVO subject",
            source_id=FDE_SOURCE,
            artifact_ids=[a["id"] for a in fde_artifacts],
        )
        fde_contract_labels = {
            "technical_evidence": "FDE Technical Evidence for RVO",
            "integration_path": "FDE Integration Path for RVO",
        }
        fde_contracts = [
            {
                "id": f"contract.fde.{artifact['type']}.rvo",
                "label": fde_contract_labels[artifact["type"]],
                "owner": ROLE_FDE,
                "artifact": artifact["id"],
            }
            for artifact in fde_artifacts
        ]
        contracts.extend(fde_contracts)
        step(
            "derive_contracts",
            "FDE-owned contracts for technical artifacts",
            owner=ROLE_FDE,
            contract_ids=[c["id"] for c in fde_contracts],
        )

    # Data Scientist loaded but excluded from v0 (role not on team).
    if DATA_SCIENTIST_SOURCE in known:
        step(
            "exclude_source",
            "Data Scientist source loaded but excluded from v0 — role not on team",
            source_id=DATA_SCIENTIST_SOURCE,
            role=ROLE_DATA_SCIENTIST,
            reason="role_not_on_team",
        )

    return {
        "artifacts": artifacts,
        "contracts": contracts,
        "trace": trace_steps,
    }


def write_interpretation(fixture_dir: Path) -> dict[str, Any]:
    """Run interpretation and write candidate files to the fixture directory."""
    fixture_dir = Path(fixture_dir)
    result = interpret_sources(fixture_dir)

    artifacts_path = fixture_dir / "artifacts.candidate.yaml"
    contracts_path = fixture_dir / "contracts.candidate.yaml"
    trace_path = fixture_dir / "interpretation_trace.json"

    with artifacts_path.open("w", encoding="utf-8") as handle:
        yaml.dump(
            {"artifacts": result["artifacts"]},
            handle,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    with contracts_path.open("w", encoding="utf-8") as handle:
        yaml.dump(
            {"contracts": result["contracts"]},
            handle,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    with trace_path.open("w", encoding="utf-8") as handle:
        json.dump(result["trace"], handle, indent=2, sort_keys=True)
        handle.write("\n")

    return result
