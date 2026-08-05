"""Two-pass assembler orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from asm.errors import AsmError
from asm.symbols import SymbolTable


@dataclass
class AssembleResult:
    """Machine code and metadata produced by a successful assemble."""

    text_words: list[int] = field(default_factory=list)
    data_bytes: bytes = b""
    symbols: SymbolTable = field(default_factory=SymbolTable)
    entry_address: int = 0


def assemble_source(source: str, *, path: str = "<stdin>") -> AssembleResult:
    """Assemble source text into machine code (two-pass)."""
    raise NotImplementedError(
        "assemble_source is not implemented yet "
        "(scaffold only — implement lexer/parser/passes next)"
    )


def assemble_file(input_path: Path) -> AssembleResult:
    """Read a file and assemble it."""
    try:
        source = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AsmError(f"cannot read input file: {exc}") from exc
    return assemble_source(source, path=str(input_path))
