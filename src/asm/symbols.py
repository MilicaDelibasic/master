"""Symbol table for labels and other named addresses."""

from __future__ import annotations

from dataclasses import dataclass, field

from asm.errors import SemanticError, SourceLocation


@dataclass(slots=True)
class Symbol:
    name: str
    address: int
    location: SourceLocation


@dataclass
class SymbolTable:
    _symbols: dict[str, Symbol] = field(default_factory=dict)

    def define(self, name: str, address: int, location: SourceLocation) -> None:
        if name in self._symbols:
            prev = self._symbols[name].location
            raise SemanticError(
                f"duplicate label '{name}' (first defined at {prev})",
                location=location,
            )
        self._symbols[name] = Symbol(name=name, address=address, location=location)

    def lookup(self, name: str) -> Symbol | None:
        return self._symbols.get(name)

    def require(self, name: str, location: SourceLocation) -> Symbol:
        symbol = self.lookup(name)
        if symbol is None:
            raise SemanticError(f"undefined label '{name}'", location=location)
        return symbol

    def items(self) -> list[Symbol]:
        return list(self._symbols.values())
