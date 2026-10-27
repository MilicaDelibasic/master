"""Lexer tests: token kinds, values, locations and lexical errors."""

from pathlib import Path

import pytest

from asm.errors import LexError
from asm.lexer import Lexer
from asm.tokens import TokenKind as K

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def lex(source: str):
    return Lexer(source, path="t.asm").tokenize()


def kinds(source: str):
    return [t.kind for t in lex(source)]


# -- happy paths ---------------------------------------------------------


def test_empty_source_is_just_eof():
    assert kinds("") == [K.EOF]


def test_blank_and_comment_lines_produce_no_tokens():
    assert kinds("\n\n   # only a comment\n\t\n") == [K.EOF]


def test_r_type_instruction():
    tokens = lex("add x3, x1, x2\n")
    assert [(t.kind, t.lexeme) for t in tokens] == [
        (K.IDENT, "add"),
        (K.IDENT, "x3"),
        (K.COMMA, ","),
        (K.IDENT, "x1"),
        (K.COMMA, ","),
        (K.IDENT, "x2"),
        (K.NEWLINE, "\n"),
        (K.EOF, ""),
    ]


def test_label_definition():
    assert kinds("loop:\n") == [K.IDENT, K.COLON, K.NEWLINE, K.EOF]


def test_label_and_instruction_on_same_line():
    assert kinds("loop: addi t0, t0, 1") == [
        K.IDENT, K.COLON, K.IDENT, K.IDENT, K.COMMA, K.IDENT, K.COMMA,
        K.INTEGER, K.NEWLINE, K.EOF,
    ]


def test_memory_operand():
    tokens = lex("lw t1, 8(sp)")
    assert [t.kind for t in tokens] == [
        K.IDENT, K.IDENT, K.COMMA, K.INTEGER, K.LPAREN, K.IDENT, K.RPAREN,
        K.NEWLINE, K.EOF,
    ]
    assert tokens[3].value == 8


def test_directives():
    tokens = lex(".text\n.data\n.word 42")
    directives = [t.lexeme for t in tokens if t.kind is K.DIRECTIVE]
    assert directives == [".text", ".data", ".word"]


def test_trailing_comment_is_skipped():
    assert kinds("nop # does nothing\n") == [K.IDENT, K.NEWLINE, K.EOF]


def test_consecutive_newlines_collapse():
    assert kinds("nop\n\n\n# c\nnop\n") == [
        K.IDENT, K.NEWLINE, K.IDENT, K.NEWLINE, K.EOF,
    ]


def test_missing_final_newline_is_added():
    assert kinds("nop") == [K.IDENT, K.NEWLINE, K.EOF]


def test_crlf_line_endings():
    assert kinds("nop\r\nnop\r\n") == [K.IDENT, K.NEWLINE, K.IDENT, K.NEWLINE, K.EOF]


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("0", 0),
        ("42", 42),
        ("-5", -5),
        ("+7", 7),
        ("0x1F", 31),
        ("0XfF", 255),
        ("-0x10", -16),
        ("0b101", 5),
        ("0xFFFFFFFF", 0xFFFFFFFF),
    ],
)
def test_integer_literals(text, value):
    token = lex(text)[0]
    assert token.kind is K.INTEGER
    assert token.lexeme == text
    assert token.value == value


def test_negative_immediate_after_comma():
    tokens = lex("addi x1, x0, -1")
    assert tokens[5].kind is K.INTEGER
    assert tokens[5].value == -1


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ('"hi"', "hi"),
        ('""', ""),
        (r'"a\nb"', "a\nb"),
        (r'"tab\there"', "tab\there"),
        (r'"q\"q"', 'q"q'),
        (r'"back\\slash"', "back\\slash"),
        (r'"nul\0"', "nul\0"),
        ('"# not a comment"', "# not a comment"),
    ],
)
def test_string_literals(text, value):
    token = lex(text)[0]
    assert token.kind is K.STRING
    assert token.lexeme == text
    assert token.value == value


def test_identifiers_may_contain_digits_underscore_and_dot():
    tokens = lex("_start my_label2 a.b")
    assert [t.lexeme for t in tokens if t.kind is K.IDENT] == ["_start", "my_label2", "a.b"]


def test_non_value_tokens_have_no_value():
    tokens = lex("add x1, x2, x3")
    assert all(t.value is None for t in tokens)


# -- locations -----------------------------------------------------------


def test_token_locations_are_one_based():
    tokens = lex("# header\n  add x3, x1, x2\n")
    add, x3, comma = tokens[0], tokens[1], tokens[2]
    assert (add.location.line, add.location.column) == (2, 3)
    assert (x3.location.line, x3.location.column) == (2, 7)
    assert (comma.location.line, comma.location.column) == (2, 9)
    assert add.location.path == "t.asm"


def test_newline_location_is_end_of_line():
    tokens = lex("nop\n")
    newline = tokens[1]
    assert (newline.location.line, newline.location.column) == (1, 4)


# -- errors --------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "message", "line", "column"),
    [
        ("add x1, x2, @", "unexpected character '@'", 1, 13),
        ("nop\n  $", "unexpected character '$'", 2, 3),
        ("addi x1, x0, 12abc", "invalid integer literal '12abc'", 1, 14),
        ("li x1, 0x", "invalid integer literal '0x'", 1, 8),
        ("li x1, 0b102", "invalid integer literal '0b102'", 1, 8),
        ("li x1, 1_000", "invalid integer literal '1_000'", 1, 8),
        ("li x1, 0xG", "invalid integer literal '0xG'", 1, 8),
        ('.asciiz "abc', "unterminated string literal", 1, 9),
        ('.asciiz "abc\n"', "unterminated string literal", 1, 9),
        (r'.asciiz "a\qb"', "unknown escape sequence '\\q'", 1, 11),
        ('.asciiz "abc\\', "unterminated string literal", 1, 9),
        (". text", "expected directive name after '.'", 1, 1),
        ("li x1, -", "unexpected character '-'", 1, 8),
    ],
)
def test_lexical_errors(source, message, line, column):
    with pytest.raises(LexError) as info:
        lex(source)
    err = info.value
    assert message in err.message
    assert (err.location.line, err.location.column) == (line, column)
    assert str(err).startswith(f"t.asm:{line}:{column}: lexical error:")


# -- examples ------------------------------------------------------------


@pytest.mark.parametrize("name", ["add.asm", "loop.asm", "memory.asm"])
def test_examples_tokenize(name):
    path = EXAMPLES / name
    tokens = Lexer(path.read_text(encoding="utf-8"), path=str(path)).tokenize()
    assert tokens[-1].kind is K.EOF
    assert tokens[-2].kind is K.NEWLINE


def test_loop_example_tokens():
    source = (EXAMPLES / "loop.asm").read_text(encoding="utf-8")
    lexemes = [t.lexeme for t in lex(source) if t.kind not in (K.NEWLINE, K.EOF)]
    assert lexemes == [
        ".text",
        "addi", "t0", ",", "x0", ",", "0",
        "addi", "t1", ",", "x0", ",", "10",
        "loop", ":",
        "addi", "t0", ",", "t0", ",", "1",
        "blt", "t0", ",", "t1", ",", "loop",
    ]
