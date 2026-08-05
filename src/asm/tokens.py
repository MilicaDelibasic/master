"""Token kinds and token records produced by the lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from asm.errors import SourceLocation


class TokenKind(Enum):
    IDENT = auto()  # mnemonic, label name, or register-like name
    DIRECTIVE = auto()  # .text, .data, .word, ...
    INTEGER = auto()
    STRING = auto()
    COMMA = auto()
    COLON = auto()
    LPAREN = auto()
    RPAREN = auto()
    NEWLINE = auto()
    EOF = auto()


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    lexeme: str
    location: SourceLocation
