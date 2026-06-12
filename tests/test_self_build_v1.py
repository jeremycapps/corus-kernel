"""Tests for the stripped Corus v1 coordination kernel."""

from __future__ import annotations

import copy
import inspect
import json
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from corus_v1.cli import main as cli_main
from corus_v1.derive import (
    DeclarationValidationError,
    derive,
    validate_declared_objects,
    with_artifact_status,
)
from corus_v1.load import REQUIRED_BUNDLE_FILES, load_project
from corus_v1.render import render

REPO_ROOT = Path(__file__).resolve().parent.parent
CORUS_DIR = REPO_ROOT / ".corus"
V1_MODULES = (
    REPO_ROOT / "corus_v1" / "load.py",
    REPO_ROOT / "corus_v1" / "derive.py",
    REPO_ROOT / "corus_v1" / "render.py",
    REPO_ROOT / "corus_v1" / "cli.py",
)

OBJECTIVE = "objective.corus_self_build_engine"
OBJECTIVE_SPEC_CONTRACT = "contract.objective_spec"
AGENT_INSTRUCTIONS_CONTRACT = "contract.agent_execution_instructions"
OBJECT_MODEL_CONTRACT = "contract.object_model_spec"
REDUCER_CONTRACT = "contract.reducer_spec"
RUNTIME_CONTRACT = "contract.runtime_status_update"
WORK_PACKET_CONTRACT = "contract.work_packet_render"
TEST_SUITE_CONTRACT = "contract.test_suite"

OBJECTIVE_SPEC = "artifact.objective_spec"
AGENT_INSTRUCTIONS = "artifact.agent_execution_instructions"
OBJECT_MODEL = "artifact.object_model_spec"
REDUCER_SPEC = "artifact.reducer_spec"
RUNTIME_STATUS = "artifact.runtime_status_update"
WORK_PACKET = "artifact.work_packet_render"
TEST_SUITE = "artifact.test_suite"


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
    for state in _derived(bundle)["contracts"]:
        if state["id"] == contract_id:
            return state
    raise KeyError(contract_id)


def _objective_state(bundle, objective_id: str = OBJECTIVE) -> dict:
    for state in _derived(bundle)["objectives"]:
        if state["id"] == objective_id:
            return state
    raise KeyError(objective_id)


def _status_bundle(bundle, statuses: dict[str, str]) -> dict:
    updated = bundle
    for artifact_id, status in statuses.items():
        updated = with_artifact_status(updated, artifact_id, status)
    return updated


def _expect_validation_error(bundle: dict, code: str) -> None:
    with pytest.raises(DeclarationValidationError) as exc:
        validate_declared_objects(bundle)
    assert any(error["code"] == code for error in exc.value.errors), exc.value.errors


def _add_multi_output_contract(bundle: dict, statuses: tuple[str, str]) -> dict:
    updated = copy.deepcopy(bundle)
    updated["artifacts"]["artifacts"].extend(
        [
            {
                "id": "artifact.multi_a",
                "requires": [],
                "status": statuses[0],
            },
            {
                "id": "artifact.multi_b",
                "requires": [],
                "status": statuses[1],
            },
        ]
    )
    updated["contracts"]["contracts"].append(
        {
            "id": "contract.multi",
            "executor": "agent.product_strategy",
            "consumer": "agent.systems_architect",
            "produces": ["artifact.multi_b", "artifact.multi_a"],
        }
    )
    updated["objectives"]["objectives"][0]["contracts"].append("contract.multi")
    return updated


def test_fixture_uses_locked_objects_only(project_bundle):
    assert set(REQUIRED_BUNDLE_FILES) == {
        "project",
        "agents",
        "objectives",
        "artifacts",
        "contracts",
    }
    assert not (CORUS_DIR / "moments.yaml").exists()

    for agent in project_bundle["agents"]["agents"]:
        assert set(agent) == {"id"}

    for objective in project_bundle["objectives"]["objectives"]:
        assert set(objective) == {"id", "intent", "agents", "contracts"}

    for contract in project_bundle["contracts"]["contracts"]:
        assert set(contract) == {"id", "executor", "consumer", "produces"}

    for artifact in project_bundle["artifacts"]["artifacts"]:
        assert set(artifact) == {"id", "requires", "status"}


def test_self_build_fixture_derives_expected_chain(project_bundle):
    assert _contract_state(project_bundle, OBJECTIVE_SPEC_CONTRACT)["readiness"] == "unblocked"
    assert _contract_state(project_bundle, AGENT_INSTRUCTIONS_CONTRACT)["readiness"] == "blocked"
    assert _contract_state(project_bundle, OBJECT_MODEL_CONTRACT)["blocked_by"] == [
        AGENT_INSTRUCTIONS,
        OBJECTIVE_SPEC,
    ]
    assert _derived(project_bundle)["next_work"]["executor_actions"][0]["contract"] == (
        OBJECTIVE_SPEC_CONTRACT
    )


# Declaration validation tests


def test_missing_objective_agent_ref_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["objectives"]["objectives"][0]["agents"][0] = "agent.missing"
    _expect_validation_error(bundle, "missing_objective_agent")


def test_missing_objective_contract_ref_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["objectives"]["objectives"][0]["contracts"][0] = "contract.missing"
    _expect_validation_error(bundle, "missing_objective_contract")


def test_missing_contract_executor_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["contracts"]["contracts"][0]["executor"] = "agent.missing"
    _expect_validation_error(bundle, "missing_contract_executor")


def test_missing_contract_consumer_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["contracts"]["contracts"][0]["consumer"] = "agent.missing"
    _expect_validation_error(bundle, "missing_contract_consumer")


def test_contract_executor_equal_to_consumer_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["contracts"]["contracts"][0]["consumer"] = bundle["contracts"]["contracts"][0]["executor"]
    _expect_validation_error(bundle, "contract_self_consumer")


def test_contract_produces_missing_artifact_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["contracts"]["contracts"][0]["produces"] = ["artifact.missing"]
    _expect_validation_error(bundle, "missing_contract_artifact")


def test_artifact_requires_missing_artifact_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["artifacts"]["artifacts"][0]["requires"] = ["artifact.missing"]
    _expect_validation_error(bundle, "missing_artifact_requirement")


def test_invalid_artifact_status_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["artifacts"]["artifacts"][0]["status"] = "draft_present"
    _expect_validation_error(bundle, "invalid_artifact_status")


def test_artifact_dependency_cycle_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    artifacts = {item["id"]: item for item in bundle["artifacts"]["artifacts"]}
    artifacts[OBJECTIVE_SPEC]["requires"] = [TEST_SUITE]
    _expect_validation_error(bundle, "artifact_dependency_cycle")


def test_duplicate_artifact_producer_within_objective_fails(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["contracts"]["contracts"].append(
        {
            "id": "contract.duplicate_objective_spec",
            "executor": "agent.systems_engineer",
            "consumer": "agent.product_strategy",
            "produces": [OBJECTIVE_SPEC],
        }
    )
    bundle["objectives"]["objectives"][0]["contracts"].append(
        "contract.duplicate_objective_spec"
    )
    _expect_validation_error(bundle, "duplicate_artifact_producer")


# Reducer readiness tests


def test_contract_with_no_artifact_requirements_is_unblocked(project_bundle):
    assert _contract_state(project_bundle, OBJECTIVE_SPEC_CONTRACT)["readiness"] == "unblocked"


def test_contract_with_all_requirements_validated_is_unblocked(project_bundle):
    bundle = _status_bundle(
        project_bundle,
        {
            OBJECTIVE_SPEC: "validated",
            AGENT_INSTRUCTIONS: "validated",
        },
    )
    assert _contract_state(bundle, OBJECT_MODEL_CONTRACT)["readiness"] == "unblocked"


@pytest.mark.parametrize("status", ["expected_missing", "present", "rejected"])
def test_contract_with_unvalidated_requirement_is_blocked(project_bundle, status):
    bundle = with_artifact_status(project_bundle, OBJECTIVE_SPEC, status)
    state = _contract_state(bundle, AGENT_INSTRUCTIONS_CONTRACT)
    assert state["readiness"] == "blocked"
    assert state["blocked_by"] == [OBJECTIVE_SPEC]


# Contract output tests


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (("expected_missing", "expected_missing"), "missing"),
        (("present", "present"), "submitted"),
        (("validated", "validated"), "satisfied"),
        (("rejected", "present"), "rejected"),
        (("present", "validated"), "partial"),
    ],
)
def test_contract_output_from_produced_artifact_statuses(project_bundle, statuses, expected):
    bundle = _add_multi_output_contract(project_bundle, statuses)
    assert _contract_state(bundle, "contract.multi")["output"] == expected


# Objective tests


def test_objective_satisfied_only_when_all_listed_contracts_satisfied(project_bundle):
    bundle = _status_bundle(
        project_bundle,
        {
            OBJECTIVE_SPEC: "validated",
            AGENT_INSTRUCTIONS: "validated",
            OBJECT_MODEL: "validated",
            REDUCER_SPEC: "validated",
            RUNTIME_STATUS: "validated",
            WORK_PACKET: "validated",
            TEST_SUITE: "validated",
        },
    )
    assert _objective_state(bundle)["satisfied"] is True
    assert _derived(bundle)["satisfied_contracts"] == [
        AGENT_INSTRUCTIONS_CONTRACT,
        OBJECT_MODEL_CONTRACT,
        OBJECTIVE_SPEC_CONTRACT,
        REDUCER_CONTRACT,
        RUNTIME_CONTRACT,
        TEST_SUITE_CONTRACT,
        WORK_PACKET_CONTRACT,
    ]


@pytest.mark.parametrize("status", ["expected_missing", "present", "rejected"])
def test_objective_unsatisfied_when_any_listed_contract_is_not_satisfied(
    project_bundle,
    status,
):
    bundle = _status_bundle(
        project_bundle,
        {
            OBJECTIVE_SPEC: "validated",
            AGENT_INSTRUCTIONS: "validated",
            OBJECT_MODEL: "validated",
            REDUCER_SPEC: "validated",
            RUNTIME_STATUS: "validated",
            WORK_PACKET: "validated",
            TEST_SUITE: status,
        },
    )
    state = _objective_state(bundle)
    assert state["satisfied"] is False
    assert TEST_SUITE_CONTRACT in state["prevented_by"]


def test_objective_unsatisfied_when_listed_contract_is_partial(project_bundle):
    bundle = _add_multi_output_contract(project_bundle, ("present", "validated"))
    bundle = _status_bundle(
        bundle,
        {
            OBJECTIVE_SPEC: "validated",
            AGENT_INSTRUCTIONS: "validated",
            OBJECT_MODEL: "validated",
            REDUCER_SPEC: "validated",
            RUNTIME_STATUS: "validated",
            WORK_PACKET: "validated",
            TEST_SUITE: "validated",
        },
    )
    state = _objective_state(bundle)
    assert state["satisfied"] is False
    assert "contract.multi" in state["prevented_by"]


def test_objective_ignores_contracts_not_listed_in_objective_contracts(project_bundle):
    bundle = copy.deepcopy(project_bundle)
    bundle["artifacts"]["artifacts"].append(
        {"id": "artifact.outside", "requires": [], "status": "expected_missing"}
    )
    bundle["contracts"]["contracts"].append(
        {
            "id": "contract.outside",
            "executor": "agent.product_strategy",
            "consumer": "agent.systems_architect",
            "produces": ["artifact.outside"],
        }
    )
    bundle = _status_bundle(
        bundle,
        {
            OBJECTIVE_SPEC: "validated",
            AGENT_INSTRUCTIONS: "validated",
            OBJECT_MODEL: "validated",
            REDUCER_SPEC: "validated",
            RUNTIME_STATUS: "validated",
            WORK_PACKET: "validated",
            TEST_SUITE: "validated",
        },
    )
    assert _objective_state(bundle)["satisfied"] is True


# Next work tests


def test_unblocked_missing_contract_appears_in_executor_actions(project_bundle):
    actions = _derived(project_bundle)["next_work"]["executor_actions"]
    assert [action["contract"] for action in actions] == [OBJECTIVE_SPEC_CONTRACT]


def test_unblocked_rejected_contract_appears_in_executor_actions(project_bundle):
    bundle = with_artifact_status(project_bundle, OBJECTIVE_SPEC, "rejected")
    actions = _derived(bundle)["next_work"]["executor_actions"]
    assert [action["contract"] for action in actions] == [OBJECTIVE_SPEC_CONTRACT]


def test_unblocked_submitted_contract_appears_in_consumer_actions(project_bundle):
    bundle = with_artifact_status(project_bundle, OBJECTIVE_SPEC, "present")
    actions = _derived(bundle)["next_work"]["consumer_actions"]
    assert [action["contract"] for action in actions] == [OBJECTIVE_SPEC_CONTRACT]


def test_blocked_contract_does_not_appear_in_executor_actions(project_bundle):
    actions = _derived(project_bundle)["next_work"]["executor_actions"]
    assert AGENT_INSTRUCTIONS_CONTRACT not in [action["contract"] for action in actions]


def test_satisfied_contract_does_not_appear_in_next_work(project_bundle):
    bundle = with_artifact_status(project_bundle, OBJECTIVE_SPEC, "validated")
    next_work = _derived(bundle)["next_work"]
    action_ids = [
        action["contract"]
        for action in next_work["executor_actions"] + next_work["consumer_actions"]
    ]
    assert OBJECTIVE_SPEC_CONTRACT not in action_ids


# Determinism tests


def test_same_fixture_produces_byte_stable_reducer_output(project_bundle):
    first = json.dumps(derive(project_bundle), indent=2, sort_keys=True)
    second = json.dumps(derive(project_bundle), indent=2, sort_keys=True)
    assert first == second


def test_changing_project_metadata_does_not_change_reducer_flow(project_bundle):
    changed = copy.deepcopy(project_bundle)
    changed["project"] = {
        "name": "Display-only rename",
        "version": "999.0",
        "description": "This metadata must not affect derived flow.",
    }
    assert derive(changed) == derive(project_bundle)


def test_ordering_of_input_lists_does_not_change_semantic_reducer_output(project_bundle):
    reordered = copy.deepcopy(project_bundle)
    for collection in ("agents", "objectives", "contracts", "artifacts"):
        reordered[collection][collection] = list(reversed(reordered[collection][collection]))
    assert derive(reordered) == derive(project_bundle)


def test_render_reads_derived_flow(project_bundle):
    output = render(project_bundle, derive(project_bundle))
    assert "Contract states" in output
    assert "readiness=unblocked, output=missing" in output
    assert "next_executor_actions" in output


def test_cli_derive_and_render(temp_project, capsys):
    code = cli_main(["derive", "--project", str(temp_project)])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert "contracts" in payload["derived"]
    assert "next_work" in payload["derived"]

    code = cli_main(["render", "--project", str(temp_project)])
    assert code == 0
    assert "Contract states" in capsys.readouterr().out


def test_modify_artifacts_yaml_changes_contract_state(temp_project):
    artifacts_path = temp_project / ".corus" / "artifacts.yaml"
    data = yaml.safe_load(artifacts_path.read_text(encoding="utf-8"))
    data["artifacts"][0]["status"] = "validated"
    artifacts_path.write_text(yaml.dump(data), encoding="utf-8")

    state = _contract_state(load_project(temp_project), AGENT_INSTRUCTIONS_CONTRACT)
    assert state["readiness"] == "unblocked"


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


def test_existing_kernel_package_unchanged():
    kernel_derive = inspect.getsource(
        __import__("corus_kernel.derive", fromlist=["derive"]).derive_context
    )
    assert "next_work" not in kernel_derive
