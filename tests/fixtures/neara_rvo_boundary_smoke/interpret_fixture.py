"""
Neara RVO fixture interpretation machinery.

Not part of the Corus declared object model. This module encodes how Neara
sources map to candidate artifacts and contracts for the v0 boundary fixture.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

RVO_SOURCE = "source.neara_rvo"
CVA_SOURCE = "source.neara_cva_job_description"
FDE_SOURCE = "source.neara_fde_job_description"
DIRECTOR_SOURCE = "source.neara_director_customer_implementation_job_description"
DATA_SCIENTIST_SOURCE = "source.neara_data_scientist_job_description"

ROLE_CVA = "role.neara_cva"
ROLE_FDE = "role.neara_fde"
ROLE_DIRECTOR = "role.neara_director_customer_implementation"
ROLE_DATA_SCIENTIST = "role.neara_data_scientist"


def _step(
    trace: list[dict[str, Any]],
    action: str,
    detail: str,
    **extra: Any,
) -> None:
    trace.append({"action": action, "detail": detail, **extra})


def interpret(
    sources: list[dict[str, Any]],
    fixture_dir: Path,
) -> dict[str, Any]:
    known = {s["id"] for s in sources}
    trace_steps: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []

    if RVO_SOURCE in known:
        _step(
            trace_steps,
            "classify_source",
            "Boundary subject intelligence, not artifact origin",
            source_id=RVO_SOURCE,
            role="boundary_subject",
        )

    if DIRECTOR_SOURCE in known:
        _step(
            trace_steps,
            "classify_source",
            (
                f"{DIRECTOR_SOURCE} supports orchestrator role "
                f"{ROLE_DIRECTOR}; no v0 artifacts derived"
            ),
            source_id=DIRECTOR_SOURCE,
            role="orchestrator_basis",
            supports_role=ROLE_DIRECTOR,
        )

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
        for artifact in cva_artifacts:
            _step(
                trace_steps,
                "derive_artifact",
                f"{artifact['id']} from {CVA_SOURCE} with subject {RVO_SOURCE}",
                artifact_id=artifact["id"],
                origin=CVA_SOURCE,
                subject=RVO_SOURCE,
            )
        for artifact in cva_artifacts:
            contracts.append(
                {
                    "id": f"contract.cva.{artifact['type']}.rvo",
                    "label": {
                        "value_evidence": "CVA Value Evidence for RVO",
                        "roi_case": "CVA ROI Case for RVO",
                    }[artifact["type"]],
                    "owner": ROLE_CVA,
                    "artifact": artifact["id"],
                }
            )
            _step(
                trace_steps,
                "derive_contract",
                (
                    f"contract.cva.{artifact['type']}.rvo assigns "
                    f"{artifact['id']} to {ROLE_CVA}"
                ),
                contract_id=f"contract.cva.{artifact['type']}.rvo",
                artifact_id=artifact["id"],
                owner=ROLE_CVA,
            )

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
        for artifact in fde_artifacts:
            _step(
                trace_steps,
                "derive_artifact",
                f"{artifact['id']} from {FDE_SOURCE} with subject {RVO_SOURCE}",
                artifact_id=artifact["id"],
                origin=FDE_SOURCE,
                subject=RVO_SOURCE,
            )
        for artifact in fde_artifacts:
            contracts.append(
                {
                    "id": f"contract.fde.{artifact['type']}.rvo",
                    "label": {
                        "technical_evidence": "FDE Technical Evidence for RVO",
                        "integration_path": "FDE Integration Path for RVO",
                    }[artifact["type"]],
                    "owner": ROLE_FDE,
                    "artifact": artifact["id"],
                }
            )
            _step(
                trace_steps,
                "derive_contract",
                (
                    f"contract.fde.{artifact['type']}.rvo assigns "
                    f"{artifact['id']} to {ROLE_FDE}"
                ),
                contract_id=f"contract.fde.{artifact['type']}.rvo",
                artifact_id=artifact["id"],
                owner=ROLE_FDE,
            )

    if DATA_SCIENTIST_SOURCE in known:
        _step(
            trace_steps,
            "exclude_source",
            (
                f"{DATA_SCIENTIST_SOURCE} was loaded but excluded "
                "from v0 boundary — role not on team"
            ),
            source_id=DATA_SCIENTIST_SOURCE,
            role=ROLE_DATA_SCIENTIST,
            reason="role_not_on_team",
        )

    return {
        "artifacts": artifacts,
        "contracts": contracts,
        "trace": trace_steps,
    }
