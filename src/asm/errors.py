"""Assembler error types with source locations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """1-based line/column in an input file (column may be None)."""

    path: str
    line: int
    column: int | None = None

    def __str__(self) -> str:
        if self.column is None:
            return f"{self.path}:{self.line}"
        return f"{self.path}:{self.line}:{self.column}"


class AsmError(Exception):
    """Base error for the assembler toolchain."""

    def __init__(
        self,
        message: str,
        *,
        location: SourceLocation | None = None,
        kind: str = "error",
    ) -> None:
        self.message = message
        self.location = location
        self.kind = kind
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.location is None:
            return f"{self.kind}: {self.message}"
        return f"{self.location}: {self.kind}: {self.message}"


class LexError(AsmError):
    def __init__(self, message: str, *, location: SourceLocation | None = None) -> None:
        super().__init__(message, location=location, kind="lexical error")


class ParseError(AsmError):
    def __init__(self, message: str, *, location: SourceLocation | None = None) -> None:
        super().__init__(message, location=location, kind="syntax error")


class SemanticError(AsmError):
    def __init__(self, message: str, *, location: SourceLocation | None = None) -> None:
        super().__init__(message, location=location, kind="semantic error")
