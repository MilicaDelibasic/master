"""Lexical analysis: source text → tokens."""

from __future__ import annotations

from asm.tokens import Token


class Lexer:
    """Hand-written lexer for the thesis assembler language."""

    def __init__(self, source: str, *, path: str = "<stdin>") -> None:
        self.source = source
        self.path = path

    def tokenize(self) -> list[Token]:
        raise NotImplementedError("Lexer.tokenize is not implemented yet")
