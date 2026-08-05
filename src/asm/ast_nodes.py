"""Lightweight AST / IR nodes between parser and code generation."""

from __future__ import annotations

from dataclasses import dataclass

from asm.errors import SourceLocation


@dataclass(slots=True)
class LabelDef:
    name: str
    location: SourceLocation


@dataclass(slots=True)
class Directive:
    name: str
    args: list[str]
    location: SourceLocation


@dataclass(slots=True)
class Instruction:
    mnemonic: str
    operands: list[str]
    location: SourceLocation


ProgramItem = LabelDef | Directive | Instruction
