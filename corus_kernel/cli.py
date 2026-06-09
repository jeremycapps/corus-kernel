"""CLI entry points for interpret and derive commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from corus_kernel.derive import derive_context
from corus_kernel.interpret import write_interpretation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="corus_kernel",
        description="Corus Kernel v0 — interpret sources and derive context",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    interpret_parser = subparsers.add_parser(
        "interpret",
        help="Interpret sources and write candidate artifacts/contracts",
    )
    interpret_parser.add_argument(
        "fixture_dir",
        type=Path,
        help="Path to fixture directory (e.g. tests/fixtures/neara_rvo_boundary_v0)",
    )

    derive_parser = subparsers.add_parser(
        "derive",
        help="Derive context from declared objects",
    )
    derive_parser.add_argument(
        "fixture_dir",
        type=Path,
        help="Path to fixture directory",
    )
    derive_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write JSON output to file (default: stdout)",
    )

    args = parser.parse_args(argv)

    if args.command == "interpret":
        result = write_interpretation(args.fixture_dir)
        print(
            f"Wrote {len(result['artifacts'])} candidate artifacts, "
            f"{len(result['contracts'])} candidate contracts",
            file=sys.stderr,
        )
        return 0

    if args.command == "derive":
        output = derive_context(args.fixture_dir)
        text = json.dumps(output, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
