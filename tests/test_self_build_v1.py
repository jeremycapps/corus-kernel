"""Tests for Corus v1 stripped agent coordination architecture."""

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
from corus_v1.load import REQUIRED_BUNDLE_FILES, default_project_dir, load_project
from corus_v1.render import render

REPO_ROOT = Path(__file__).resolve().parent.parent
CORUS_DIR = REPO_ROOT / ".corus"
V1_MODULES = (
    REPO_ROOT / "corus_v1" / "load.py",
    REPO_ROOT / "corus_v1" / "derive.py",
    REPO_ROOT / "corus_v1" / "render.py",
    REPO_ROOT / "corus_v1" / "cli.py",
)

OBJECTIVE_SPEC_CONTRACT = "contract.objective_spec"
ARCHITECTURE_CONTRACT = "contract.architecture_spec"
REDUCER_CONTRACT = "contract.reducer_implementation"
SURFACE_CONTRACT = "contract.surface_rendering"

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


def _derived(bundle):
    return derive(bundle)["derived"]


def _contract_state(bundle, contract_id: str) -> dict:
    for state in _derived(bundle)["contract_states"]:
        if state["id"] == contract_id:
            return state
    raise KeyError(contract_id)


# 1. initial fixture


def test_initial_fixture_contract_states(project_bundle):
    objective = _contract_state(project_bundle, OBJECTIVE_SPEC_CONTRACT)
    architecture = _contract_state(project_bundle, ARCHITECTURE_CONTRACT)
    reducer = _contract_state(project_bundle, REDUCER_CONTRACT)
    surface = _contract_state(project_bundle, SURFACE_CONTRACT)

    assert objective["readiness"] == "unblocked"
    assert objective["output"] == "missing"
    assert architecture["readiness"] == "blocked"
    assert reducer["readiness"] == "blocked"
    assert surface["readiness"] == "blocked"
    assert _derived(project_bundle)["blocked_contracts"] == [
        ARCHITECTURE_CONTRACT,
        REDUCER_CONTRACT,
        SURFACE_CONTRACT,
    ]


# 2. objective_spec present


def test_objective_spec_present_submits_output_and_keeps_downstream_blocked(temp_project):
    bundle = with_artifact_status(load_project(temp_project), OBJECTIVE_SPEC, "present")
    derived = _derived(bundle)

    assert _contract_state(bundle, OBJECTIVE_SPEC_CONTRACT)["output"] == "submitted"
    assert _contract_state(bundle, ARCHITECTURE_CONTRACT)["readiness"] == "blocked"
    assert derived["submitted_contracts"] == [OBJECTIVE_SPEC_CONTRACT]
    assert derived["satisfied_objectives"] == []


# 3. objective_spec validated


def test_objective_spec_validated_satisfies_contract_and_unblocks_architecture(temp_project):
    bundle = with_artifact_status(load_project(temp_project), OBJECTIVE_SPEC, "validated")
    derived = _derived(bundle)

    assert _contract_state(bundle, OBJECTIVE_SPEC_CONTRACT)["output"] == "satisfied"
    assert _contract_state(bundle, ARCHITECTURE_CONTRACT)["readiness"] == "unblocked"
    assert OBJECTIVE_SPEC_CONTRACT in derived["satisfied_contracts"]
    assert derived["satisfied_objectives"] == []


# 4. architecture_spec present


def test_architecture_spec_present_submits_output_and_keeps_downstream_blocked(temp_project):
    bundle = load_project(temp_project)
    bundle = with_artifact_status(bundle, OBJECTIVE_SPEC, "validated")
    bundle = with_artifact_status(bundle, ARCHITECTURE_SPEC, "present")
    derived = _derived(bundle)

    assert _contract_state(bundle, ARCHITECTURE_CONTRACT)["output"] == "submitted"
    assert _contract_state(bundle, REDUCER_CONTRACT)["readiness"] == "blocked"
    assert _contract_state(bundle, SURFACE_CONTRACT)["readiness"] == "blocked"
    assert derived["satisfied_objectives"] == []


# 5. architecture_spec validated


def test_architecture_spec_validated_satisfies_contract_and_unblocks_reducer(temp_project):
    bundle = load_project(temp_project)
    bundle = with_artifact_status(bundle, OBJECTIVE_SPEC, "validated")
    bundle = with_artifact_status(bundle, ARCHITECTURE_SPEC, "validated")
    derived = _derived(bundle)

    assert _contract_state(bundle, ARCHITECTURE_CONTRACT)["output"] == "satisfied"
    assert _contract_state(bundle, REDUCER_CONTRACT)["readiness"] == "unblocked"
    assert _contract_state(bundle, SURFACE_CONTRACT)["readiness"] == "blocked"


# 6. reducer_implementation present


def test_reducer_implementation_present_submits_output_and_keeps_surface_blocked(temp_project):
    bundle = load_project(temp_project)
    bundle = with_artifact_status(bundle, OBJECTIVE_SPEC, "validated")
    bundle = with_artifact_status(bundle, ARCHITECTURE_SPEC, "validated")
    bundle = with_artifact_status(bundle, REDUCER, "present")
    derived = _derived(bundle)

    assert _contract_state(bundle, REDUCER_CONTRACT)["output"] == "submitted"
    assert _contract_state(bundle, SURFACE_CONTRACT)["readiness"] == "blocked"
    assert derived["satisfied_objectives"] == []


# 7. reducer_implementation validated


def test_reducer_implementation_validated_satisfies_contract_and_unblocks_surface(temp_project):
    bundle = load_project(temp_project)
    bundle = with_artifact_status(bundle, OBJECTIVE_SPEC, "validated")
    bundle = with_artifact_status(bundle, ARCHITECTURE_SPEC, "validated")
    bundle = with_artifact_status(bundle, REDUCER, "validated")
    derived = _derived(bundle)

    assert _contract_state(bundle, REDUCER_CONTRACT)["output"] == "satisfied"
    assert _contract_state(bundle, SURFACE_CONTRACT)["readiness"] == "unblocked"
    assert derived["satisfied_objectives"] == []


# 8. all artifacts validated


def test_all_artifacts_validated_satisfies_objective_and_clears_blocked_work(temp_project):
    bundle = load_project(temp_project)
    for artifact_id in (OBJECTIVE_SPEC, ARCHITECTURE_SPEC, REDUCER, SURFACES):
        bundle = with_artifact_status(bundle, artifact_id, "validated")

    derived = _derived(bundle)

    assert all(
        _contract_state(bundle, contract_id)["output"] == "satisfied"
        for contract_id in (
            OBJECTIVE_SPEC_CONTRACT,
            ARCHITECTURE_CONTRACT,
            REDUCER_CONTRACT,
            SURFACE_CONTRACT,
        )
    )
    assert derived["satisfied_contracts"] == [
        OBJECTIVE_SPEC_CONTRACT,
        ARCHITECTURE_CONTRACT,
        REDUCER_CONTRACT,
        SURFACE_CONTRACT,
    ]
    assert derived["blocked_contracts"] == []
    assert len(derived["satisfied_objectives"]) == 1
    assert derived["active_objectives"] == []


def test_bundle_does_not_require_validations_yaml():
    assert "validations" not in REQUIRED_BUNDLE_FILES
    assert not (CORUS_DIR / "validations.yaml").exists()
    bundle = load_project(REPO_ROOT)
    assert "validations" not in bundle


def test_declared_objects_store_identity_and_status_only(project_bundle):
    for agent in project_bundle["agents"]["agents"]:
        assert set(agent.keys()) == {"id", "label"}

    for artifact in project_bundle["artifacts"]["artifacts"]:
        assert set(artifact.keys()) == {"id", "status"}

    for objective in project_bundle["objectives"]["objectives"]:
        assert "intent" in objective
        assert "contracts" in objective
        assert "depends_on" not in objective

    for contract in project_bundle["contracts"]["contracts"]:
        assert {"owner", "executor", "consumer", "requires", "produces"}.issubset(contract)
        assert "depends_on" not in contract
        assert "artifact" not in contract


def test_readiness_depends_only_on_requires(project_bundle):
    bundle = with_artifact_status(project_bundle, OBJECTIVE_SPEC, "present")
    assert _contract_state(bundle, ARCHITECTURE_CONTRACT)["readiness"] == "blocked"


def test_output_depends_only_on_produces(project_bundle):
    bundle = with_artifact_status(project_bundle, OBJECTIVE_SPEC, "present")
    assert _contract_state(bundle, OBJECTIVE_SPEC_CONTRACT)["output"] == "submitted"
    assert _contract_state(bundle, OBJECTIVE_SPEC_CONTRACT)["readiness"] == "unblocked"


def test_render_reads_contract_states(project_bundle):
    output = render(project_bundle, derive(project_bundle))
    assert "Contract states" in output
    assert "readiness=unblocked, output=missing" in output
    assert "Contracts instruct. Artifacts report. Reducers derive." in output


def test_changing_artifact_status_changes_contract_state_deterministically(temp_project):
    bundle = load_project(temp_project)
    before = _contract_state(bundle, ARCHITECTURE_CONTRACT)
    after = _contract_state(
        with_artifact_status(bundle, OBJECTIVE_SPEC, "validated"),
        ARCHITECTURE_CONTRACT,
    )

    assert before["readiness"] == "blocked"
    assert after["readiness"] == "unblocked"

    repeat = _contract_state(
        with_artifact_status(bundle, OBJECTIVE_SPEC, "validated"),
        ARCHITECTURE_CONTRACT,
    )
    assert repeat == after


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
    payload = json.loads(capsys.readouterr().out)
    assert "contract_states" in payload["derived"]

    code = cli_main(["render", "--project", str(temp_project)])
    assert code == 0
    assert "Contract states" in capsys.readouterr().out


def test_modify_artifacts_yaml_changes_contract_state(temp_project):
    artifacts_path = temp_project / ".corus" / "artifacts.yaml"
    data = yaml.safe_load(artifacts_path.read_text(encoding="utf-8"))
    data["artifacts"][0]["status"] = "validated"
    artifacts_path.write_text(yaml.dump(data), encoding="utf-8")

    state = _contract_state(load_project(temp_project), ARCHITECTURE_CONTRACT)
    assert state["readiness"] == "unblocked"


def test_existing_kernel_package_unchanged():
    kernel_derive = inspect.getsource(
        __import__("corus_kernel.derive", fromlist=["derive"]).derive_context
    )
    assert "contract_states" not in kernel_derive
