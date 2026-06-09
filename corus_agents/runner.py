"""Agent runtime CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from corus_agents import admission_agent, audit_agent, derive_agent, interpreter_agent, surface_agent
from corus_agents.workflow import admission_required, review_required, run_pipeline

KNOWN_RUN_TASKS = frozenset({
    "interpret",
    "admission-report",
    "derive",
    "audit",
    "explain",
})


def _run_interpret(fixture_dir: Path) -> int:
    result = interpreter_agent.run(fixture_dir)
    print(
        f"Wrote {result.outputs['artifact_count']} candidate artifacts, "
        f"{result.outputs['contract_count']} candidate contracts",
        file=sys.stderr,
    )
    if admission_required(fixture_dir):
        print(
            "Admission review required before derive. "
            "Run: corus_agents admit <fixture> --approve",
            file=sys.stderr,
        )
        return 2
    return 0


def _run_admission_report(fixture_dir: Path, *, approve: bool) -> int:
    result = admission_agent.run(fixture_dir, approve=approve)
    if result.outputs["promoted"]:
        print("Promoted candidates to admitted YAML.", file=sys.stderr)
        return 0
    print(f"Wrote admission report: {result.outputs['admission_report']}", file=sys.stderr)
    if review_required(fixture_dir):
        print(
            "Review required: candidates differ from admitted YAML. "
            "Run: corus_agents admit <fixture> --approve",
            file=sys.stderr,
        )
        return 2
    return 0


def _run_derive(fixture_dir: Path, *, boundary: str | None, output: Path | None) -> int:
    try:
        result = derive_agent.run(
            fixture_dir,
            boundary_id=boundary,
            output_path=output,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Wrote derive output: {result.outputs['derive_output']}", file=sys.stderr)
    return 0


def _run_audit(fixture_dir: Path, *, boundary: str | None) -> int:
    result = audit_agent.run(fixture_dir, boundary_id=boundary)
    status = "PASSED" if result.outputs["passed"] else "FAILED"
    print(
        f"Audit {status}: {result.outputs['audit_report']} "
        f"({result.outputs['error_count']} issues)",
        file=sys.stderr,
    )
    return 0 if result.outputs["passed"] else 1


def _run_explain(fixture_dir: Path, *, derive_path: Path | None) -> int:
    result = surface_agent.run(fixture_dir, derive_path=derive_path)
    print(result.outputs["readout"])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="corus_agents",
        description="Corus Agents — runtime workers that operate the kernel pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run pipeline or a single agent task",
    )
    run_parser.add_argument("first", type=str, help="Fixture dir or task name")
    run_parser.add_argument("second", type=Path, nargs="?", default=None)
    run_parser.add_argument("--boundary", default=None)
    run_parser.add_argument("-o", "--output", type=Path, default=None)
    run_parser.add_argument(
        "--derive-path",
        type=Path,
        default=None,
        help="Path to derive JSON for explain task",
    )

    admit_parser = subparsers.add_parser(
        "admit",
        help="Run admission report and optionally promote candidates",
    )
    admit_parser.add_argument("fixture_dir", type=Path)
    admit_parser.add_argument(
        "--approve",
        action="store_true",
        help="Promote candidates to admitted YAML after explicit review",
    )

    args = parser.parse_args(argv)

    if args.command == "admit":
        if not args.approve:
            result = admission_agent.run(args.fixture_dir, approve=False)
            print(f"Wrote admission report: {result.outputs['admission_report']}", file=sys.stderr)
            if review_required(args.fixture_dir):
                print(
                    "Review required. Re-run with --approve after explicit review.",
                    file=sys.stderr,
                )
                return 2
            return 0
        admission_agent.run(args.fixture_dir, approve=True)
        print("Promoted candidates to admitted YAML.", file=sys.stderr)
        return 0

    if args.command == "run":
        if args.first in KNOWN_RUN_TASKS:
            if args.second is None:
                print(f"Task '{args.first}' requires a fixture directory.", file=sys.stderr)
                return 1
            fixture_dir = args.second
            if args.first == "interpret":
                return _run_interpret(fixture_dir)
            if args.first == "admission-report":
                return _run_admission_report(fixture_dir, approve=False)
            if args.first == "derive":
                return _run_derive(fixture_dir, boundary=args.boundary, output=args.output)
            if args.first == "audit":
                return _run_audit(fixture_dir, boundary=args.boundary)
            if args.first == "explain":
                return _run_explain(fixture_dir, derive_path=args.derive_path)

        fixture_dir = Path(args.first)
        if not fixture_dir.is_dir():
            print(f"Not a fixture directory: {fixture_dir}", file=sys.stderr)
            return 1
        code, message = run_pipeline(fixture_dir, boundary_id=args.boundary)
        print(message, file=sys.stderr)
        return code

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
