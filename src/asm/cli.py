"""Command-line interface for the assembler."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from asm import __version__
from asm.assembler import assemble_file
from asm.errors import AsmError
from asm.output import write_bin, write_hex


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asm",
        description="Two-pass assembler for a RISC-V RV32I subset.",
    )
    parser.add_argument("input", type=Path, help="Input assembly file (.asm)")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("out"),
        help="Directory for .bin / .hex outputs (default: out)",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path: Path = args.input
    output_dir: Path = args.output_dir

    if not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        result = assemble_file(input_path)
    except NotImplementedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except AsmError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    write_bin(output_dir / f"{stem}.bin", result.text_words)
    write_hex(output_dir / f"{stem}.hex", result.text_words)
    print(f"Wrote {output_dir / (stem + '.bin')} and {output_dir / (stem + '.hex')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
