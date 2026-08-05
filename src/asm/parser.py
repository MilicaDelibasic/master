"""Syntax analysis: tokens → program items."""

from __future__ import annotations

from asm.ast_nodes import ProgramItem
from asm.tokens import Token


class Parser:
    """Hand-written parser (feeds the two-pass assembler)."""

    def __init__(self, tokens: list[Token], *, path: str = "<stdin>") -> None:
        self.tokens = tokens
        self.path = path

    def parse(self) -> list[ProgramItem]:
        raise NotImplementedError("Parser.parse is not implemented yet")
