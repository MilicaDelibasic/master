"""Assembler directives (.text, .data, .word, ...)."""

from __future__ import annotations

# Names recognized in pass 1 / pass 2 (implementation fills behavior later).
SECTION_DIRECTIVES = frozenset({".text", ".data"})
DATA_DIRECTIVES = frozenset({".word", ".byte", ".asciiz", ".ascii", ".space"})
SUPPORTED_DIRECTIVES = SECTION_DIRECTIVES | DATA_DIRECTIVES
