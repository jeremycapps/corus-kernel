"""Corus v1 self-build CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from corus_v1.derive import derive
from corus_v1.load import default_project_dir, load_project
from corus_v1.render import render


def _run_derive(project_dir: Path, *, output: Path | None) -> int:
    bundle = load_project(project_dir)
    result = derive(bundle)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if output:
        output.write_text(payload, encoding="utf-8")
        print(f"Wrote derive output: {output}", file=sys.stderr)
    else:
        print(payload, end="")
    return 0


def _run_render(project_dir: Path, *, derive_path: Path | None, output: Path | None) -> int:
    bundle = load_project(project_dir)
    if derive_path:
        result = json.loads(derive_path.read_text(encoding="utf-8"))
    else:
        result = derive(bundle)
    text = render(bundle, result)
    if output:
        output.write_text(text, encoding="utf-8")
        print(f"Wrote render output: {output}", file=sys.stderr)
    else:
        print(text, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="corus_v1",
        description="Corus v1 self-build derive and render",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    derive_parser = subparsers.add_parser("derive", help="Derive self-build state")
    derive_parser.add_argument(
        "--project",
        type=Path,
        default=default_project_dir(),
        help="Project directory containing .corus/",
    )
    derive_parser.add_argument("-o", "--output", type=Path, default=None)

    render_parser = subparsers.add_parser("render", help="Render derived contract states")
    render_parser.add_argument(
        "--project",
        type=Path,
        default=default_project_dir(),
        help="Project directory containing .corus/",
    )
    render_parser.add_argument(
        "--derive-path",
        type=Path,
        default=None,
        help="Optional derive JSON input",
    )
    render_parser.add_argument("-o", "--output", type=Path, default=None)

    args = parser.parse_args(argv)

    if args.command == "derive":
        return _run_derive(args.project, output=args.output)
    if args.command == "render":
        return _run_render(
            args.project,
            derive_path=args.derive_path,
            output=args.output,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
