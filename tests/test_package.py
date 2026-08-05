"""Smoke tests for package imports and error formatting."""

from asm import __version__
from asm.errors import AsmError, SourceLocation
from asm.symbols import SymbolTable


def test_version():
    assert __version__ == "0.1.0"


def test_asm_error_with_location():
    loc = SourceLocation("examples/add.asm", 3, 5)
    err = AsmError("unexpected token", location=loc)
    assert str(err) == "examples/add.asm:3:5: error: unexpected token"


def test_symbol_table_define_and_lookup():
    table = SymbolTable()
    loc = SourceLocation("t.asm", 1)
    table.define("loop", 0x100, loc)
    assert table.require("loop", loc).address == 0x100


def test_symbol_table_duplicate():
    table = SymbolTable()
    loc1 = SourceLocation("t.asm", 1)
    loc2 = SourceLocation("t.asm", 2)
    table.define("loop", 0, loc1)
    try:
        table.define("loop", 4, loc2)
        assert False, "expected SemanticError"
    except Exception as exc:
        assert "duplicate label" in str(exc)
