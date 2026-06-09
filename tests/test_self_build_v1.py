"""Tests for Corus v1 self-build derive and render."""

from __future__ import annotations

import inspect
import json
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_v1.cli import main as cli_main
from corus_v1.derive import derive, with_artifact_status
from corus_v1.load import default_project_dir, load_project
from corus_v1.render import render

REPO_ROOT = Path(__file__).resolve().parent.parent
CORUS_DIR = REPO_ROOT / ".corus"
V1_MODULES = (
    REPO_ROOT / "corus_v1" / "load.py",
    REPO_ROOT / "corus_v1" / "derive.py",
    REPO_ROOT / "corus_v1" / "render.py",
    REPO_ROOT / "corus_v1" / "cli.py",
)

PRODUCT_CONTRACT = "contract.product_strategy.objective_spec"
ARCHITECTURE_CONTRACT = "contract.systems_architecture.architecture_spec"
ENGINEER_CONTRACT = "contract.systems_engineer.reducer"
UI_CONTRACT = "contract.ui_ux.surface_rendering"

OBJECTIVE_SPEC = "artifact.objective_spec"
ARCHITECTURE_SPEC = "artifact.architecture_spec"
REDUCER = "artifact.reducer_implementation"
SURFACES = "artifact.surface_rendering"


@pytest.fixture
def project_bundle():
    return load_project(REPO_ROOT)


@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(CORUS_DIR, tmp_path / ".corus")
        yield tmp_path


def _agent_ids(items: list[dict], key: str = "agent_id") -> set[str]:
    return {item[key] for item in items}


def _derived(bundle):
    return derive(bundle)["derived"]


def _validation_for(bundle, artifact_id: str) -> list[dict]:
    return [
        item for item in _derived(bundle)["validations_required"]
        if item["artifact"] == artifact_id
    ]


def _contract_active(bundle, contract_id: str) -> bool:
    return any(item["id"] == contract_id for item in _derived(bundle)["active_contracts"])


def _contract_satisfied(bundle, contract_id: str) -> bool:
    return any(item["id"] == contract_id for item in _derived(bundle)["satisfied_contracts"])


# 1. initial fixture unblocks Product Strategy only


def test_initial_fixture_unblocks_product_strategy_only(project_bundle):
    derived = _derived(project_bundle)

    assert _agent_ids(derived["unblocked_executors"]) == {"agent.product_strategy"}
    assert _agent_ids(derived["blocked_executors"]) == {
        "agent.systems_architecture",
        "agent.systems_engineer",
        "agent.ui_ux",
    }
    assert derived["submitted_artifacts"] == []
    assert derived["validations_required"] == []
    assert derived["satisfied_contracts"] == []
    assert derived["satisfied_objectives"] == []


# 2. objective_spec present requires validation


def test_objective_spec_present_requires_validation(temp_project):
    bundle = with_artifact_status(load_project(temp_project), OBJECTIVE_SPEC, "present")
    derived = _derived(bundle)

    assert _validation_for(bundle, OBJECTIVE_SPEC)
    assert derived["validations_required"][0]["required_status"] == "validated"


# 3. objective_spec present does not satisfy product contract


def test_objective_spec_present_does_not_satisfy_product_contract(temp_project):
    bundle = with_artifact_status(load_project(temp_project), OBJECTIVE_SPEC, "present")
    derived = _derived(bundle)

    assert _contract_active(bundle, PRODUCT_CONTRACT)
    assert not _contract_satisfied(bundle, PRODUCT_CONTRACT)
    assert any(item["id"] == "objective.product_strategy_spec" for item in derived["active_objectives"])
    assert not any(item["id"] == "objective.product_strategy_spec" for item in derived["satisfied_objectives"])


# 4. objective_spec validated unblocks Systems Architecture


def test_objective_spec_validated_unblocks_systems_architecture(temp_project):
    bundle = with_artifact_status(load_project(temp_project), OBJECTIVE_SPEC, "validated")
    derived = _derived(bundle)

    assert _contract_satisfied(bundle, PRODUCT_CONTRACT)
    assert _agent_ids(derived["unblocked_executors"]) == {"agent.systems_architecture"}
    assert _agent_ids(derived["blocked_executors"]) == {
        "agent.systems_engineer",
        "agent.ui_ux",
    }


# 5. architecture_spec present requires validation


def test_architecture_spec_present_requires_validation(temp_project):
    bundle = load_project(temp_project)
    bundle = with_artifact_status(bundle, OBJECTIVE_SPEC, "validated")
    bundle = with_artifact_status(bundle, ARCHITECTURE_SPEC, "present")
    derived = _derived(bundle)

    assert _validation_for(bundle, ARCHITECTURE_SPEC)
    assert derived["validations_required"][0]["artifact"] == ARCHITECTURE_SPEC


# 6. architecture_spec present does not unblock Systems Engineer/UI


def test_architecture_spec_present_does_not_unblock_engineer_or_ui(temp_project):
    bundle = load_project(temp_project)
    bundle = with_artifact_status(bundle, OBJECTIVE_SPEC, "validated")
    bundle = with_artifact_status(bundle, ARCHITECTURE_SPEC, "present")
    derived = _derived(bundle)

    assert _contract_active(bundle, ARCHITECTURE_CONTRACT)
    assert not _contract_satisfied(bundle, ARCHITECTURE_CONTRACT)
    assert _agent_ids(derived["unblocked_executors"]) == {"agent.systems_architecture"}
    assert _agent_ids(derived["blocked_executors"]) == {
        "agent.systems_engineer",
        "agent.ui_ux",
    }


# 7. architecture_spec validated unblocks Systems Engineer and UI/UX


def test_architecture_spec_validated_unblocks_engineer_and_ui(temp_project):
    bundle = load_project(temp_project)
    bundle = with_artifact_status(bundle, OBJECTIVE_SPEC, "validated")
    bundle = with_artifact_status(bundle, ARCHITECTURE_SPEC, "validated")
    derived = _derived(bundle)

    assert _contract_satisfied(bundle, ARCHITECTURE_CONTRACT)
    assert _agent_ids(derived["unblocked_executors"]) == {
        "agent.systems_engineer",
        "agent.ui_ux",
    }
    assert derived["blocked_executors"] == []


# 8. all artifacts validated satisfies all objectives


def test_all_artifacts_validated_satisfies_all_objectives(temp_project):
    bundle = load_project(temp_project)
    for artifact_id in (OBJECTIVE_SPEC, ARCHITECTURE_SPEC, REDUCER, SURFACES):
        bundle = with_artifact_status(bundle, artifact_id, "validated")

    derived = _derived(bundle)

    assert len(derived["satisfied_contracts"]) == 4
    assert derived["active_contracts"] == []
    assert len(derived["satisfied_objectives"]) == 4
    assert derived["active_objectives"] == []
    assert derived["validations_required"] == []
    assert derived["blocked_executors"] == []
    assert derived["unblocked_executors"] == []


def test_load_self_build_fixture(project_bundle):
    assert project_bundle["project"]["name"] == "Corus v1 Self-Build"
    assert len(project_bundle["agents"]["agents"]) == 4
    assert len(project_bundle["objectives"]["objectives"]) == 4


def test_render_shows_coordinate_implement_value_surfaces(project_bundle):
    result = derive(project_bundle)
    output = render(project_bundle, result)

    assert "Coordinate surface" in output
    assert "Implement surface" in output
    assert "Value surface" in output


def test_render_reflects_validated_objective_spec_state(temp_project):
    bundle = with_artifact_status(load_project(temp_project), OBJECTIVE_SPEC, "validated")
    output = render(bundle, derive(bundle))

    assert "  - unblocked: Systems Architecture" in output
    assert "  - blocked: Systems Engineer" in output
    assert "  - blocked: UI/UX" in output


def test_changing_artifact_status_changes_executor_state_deterministically(temp_project):
    bundle = load_project(temp_project)
    before = derive(bundle)
    after = derive(with_artifact_status(bundle, OBJECTIVE_SPEC, "validated"))

    assert before["derived"]["blocked_executors"] != after["derived"]["blocked_executors"]
    assert before["derived"]["unblocked_executors"] != after["derived"]["unblocked_executors"]

    repeat = derive(with_artifact_status(bundle, OBJECTIVE_SPEC, "validated"))
    assert repeat["derived"]["blocked_executors"] == after["derived"]["blocked_executors"]
    assert repeat["derived"]["unblocked_executors"] == after["derived"]["unblocked_executors"]


def test_no_neara_specific_ids_in_v1_code():
    forbidden = ("source.neara", "artifact.value_evidence", "neara_rvo")
    for path in V1_MODULES:
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{token} found in {path.name}"


def test_no_llm_or_network_calls_in_v1_code():
    forbidden = ("openai", "anthropic", "requests.get", "urllib.request", "httpx")
    for path in V1_MODULES:
        source = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in source, f"{token} found in {path.name}"


def test_cli_derive_and_render(temp_project, capsys):
    code = cli_main(["derive", "--project", str(temp_project)])
    assert code == 0
    assert "derived" in json.loads(capsys.readouterr().out)

    code = cli_main(["render", "--project", str(temp_project)])
    assert code == 0
    assert "Coordinate surface" in capsys.readouterr().out


def test_modify_artifacts_yaml_changes_derive_state(temp_project):
    artifacts_path = temp_project / ".corus" / "artifacts.yaml"
    data = yaml.safe_load(artifacts_path.read_text(encoding="utf-8"))
    data["artifacts"][0]["status"] = "validated"
    artifacts_path.write_text(yaml.dump(data), encoding="utf-8")

    derived = _derived(load_project(temp_project))
    assert _agent_ids(derived["unblocked_executors"]) == {"agent.systems_architecture"}


def test_existing_kernel_package_unchanged():
    kernel_derive = inspect.getsource(
        __import__("corus_kernel.derive", fromlist=["derive"]).derive_context
    )
    assert "active_objectives" not in kernel_derive
