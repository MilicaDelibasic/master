"""Lexical analysis: source text → tokens.

Lexical rules (thesis chapter 5):

- Comments start with ``#`` and run to the end of the line.
- Identifiers: ``[A-Za-z_][A-Za-z0-9_.]*`` (mnemonics, labels, registers).
- Directives: ``.`` followed by an identifier (``.text``, ``.word``, ...).
- Integers: decimal, ``0x`` hex or ``0b`` binary, optional leading ``-``/``+``.
- Strings: double-quoted, escapes ``\\n \\t \\r \\0 \\\\ \\"``.
- Punctuation: ``,`` ``:`` ``(`` ``)``.
- Spaces, tabs and ``\\r`` are skipped.

NEWLINE tokens separate statements: blank and comment-only lines produce
none, so the stream never starts with NEWLINE or contains two in a row, and
every non-empty stream ends with ``NEWLINE EOF``.
"""

from __future__ import annotations

from asm.errors import LexError, SourceLocation
from asm.tokens import Token, TokenKind

_PUNCTUATION = {
    ",": TokenKind.COMMA,
    ":": TokenKind.COLON,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
}

_DIGITS = {2: "01", 10: "0123456789", 16: "0123456789abcdef"}

_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\", '"': '"'}


# ch is "" at end of input; note that `"" in "_."` is True, hence ch == "_" etc.
def _is_ident_start(ch: str) -> bool:
    return ch.isascii() and (ch.isalpha() or ch == "_")


def _is_ident_char(ch: str) -> bool:
    return ch.isascii() and (ch.isalnum() or ch == "_" or ch == ".")


class Lexer:
    """Hand-written lexer for the thesis assembler language."""

    def __init__(self, source: str, *, path: str = "<stdin>") -> None:
        self.source = source
        self.path = path
        self._pos = 0
        self._line = 1
        self._col = 1
        self._tokens: list[Token] = []

    # -- cursor helpers -------------------------------------------------

    def _peek(self, offset: int = 0) -> str:
        i = self._pos + offset
        return self.source[i] if i < len(self.source) else ""

    def _advance(self) -> str:
        ch = self.source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _location(self) -> SourceLocation:
        return SourceLocation(self.path, self._line, self._col)

    def _emit(
        self,
        kind: TokenKind,
        lexeme: str,
        location: SourceLocation,
        value: int | str | None = None,
    ) -> None:
        self._tokens.append(Token(kind, lexeme, location, value))

    def _emit_newline(self, location: SourceLocation) -> None:
        # Collapse blank lines: only terminate a statement that has tokens.
        if self._tokens and self._tokens[-1].kind is not TokenKind.NEWLINE:
            self._emit(TokenKind.NEWLINE, "\n", location)

    # -- main loop ------------------------------------------------------

    def tokenize(self) -> list[Token]:
        """Convert the whole source into a token list ending with EOF."""
        self._pos, self._line, self._col = 0, 1, 1
        self._tokens = []

        while self._pos < len(self.source):
            ch = self._peek()
            if ch in " \t\r":
                self._advance()
            elif ch == "#":
                while self._pos < len(self.source) and self._peek() != "\n":
                    self._advance()
            elif ch == "\n":
                loc = self._location()
                self._advance()
                self._emit_newline(loc)
            elif ch in _PUNCTUATION:
                loc = self._location()
                self._advance()
                self._emit(_PUNCTUATION[ch], ch, loc)
            elif ch == ".":
                self._lex_directive()
            elif _is_ident_start(ch):
                self._lex_identifier()
            elif ch.isdigit() or (ch in "+-" and self._peek(1).isdigit()):
                self._lex_integer()
            elif ch == '"':
                self._lex_string()
            else:
                raise LexError(f"unexpected character {ch!r}", location=self._location())

        end = self._location()
        self._emit_newline(end)
        self._emit(TokenKind.EOF, "", end)
        return self._tokens

    # -- token rules ----------------------------------------------------

    def _read_word(self) -> str:
        """Consume identifier characters and return them."""
        start = self._pos
        while _is_ident_char(self._peek()):
            self._advance()
        return self.source[start : self._pos]

    def _lex_identifier(self) -> None:
        loc = self._location()
        self._emit(TokenKind.IDENT, self._read_word(), loc)

    def _lex_directive(self) -> None:
        loc = self._location()
        self._advance()  # '.'
        if not _is_ident_start(self._peek()):
            raise LexError("expected directive name after '.'", location=loc)
        self._emit(TokenKind.DIRECTIVE, "." + self._read_word(), loc)

    def _lex_integer(self) -> None:
        loc = self._location()
        start = self._pos
        sign = 1
        if self._peek() in "+-":
            sign = -1 if self._advance() == "-" else 1

        base = 10
        if self._peek() == "0" and self._peek(1) in ("x", "X", "b", "B"):
            base = 16 if self._peek(1) in "xX" else 2
            self._advance()
            self._advance()

        digits_start = self._pos
        # Read the whole alphanumeric run so "12abc" is one bad literal,
        # not INTEGER 12 followed by IDENT abc.
        while _is_ident_char(self._peek()):
            self._advance()
        digits = self.source[digits_start : self._pos]
        lexeme = self.source[start : self._pos]

        # Explicit digit check: int() alone would also accept "1_000".
        if not digits or any(c not in _DIGITS[base] for c in digits.lower()):
            raise LexError(f"invalid integer literal '{lexeme}'", location=loc)
        self._emit(TokenKind.INTEGER, lexeme, loc, sign * int(digits, base))

    def _lex_string(self) -> None:
        loc = self._location()
        start = self._pos
        self._advance()  # opening quote
        chars: list[str] = []
        while True:
            ch = self._peek()
            if ch in ("", "\n"):
                raise LexError("unterminated string literal", location=loc)
            if ch == '"':
                self._advance()
                break
            if ch == "\\":
                esc_loc = self._location()
                self._advance()
                esc = self._peek()
                if esc in ("", "\n"):
                    raise LexError("unterminated string literal", location=loc)
                if esc not in _ESCAPES:
                    raise LexError(f"unknown escape sequence '\\{esc}'", location=esc_loc)
                self._advance()
                chars.append(_ESCAPES[esc])
            else:
                chars.append(self._advance())
        self._emit(TokenKind.STRING, self.source[start : self._pos], loc, "".join(chars))
