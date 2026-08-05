"""Encode RISC-V RV32I instructions into 32-bit machine words."""

from __future__ import annotations

# Placeholder opcode map — filled when the ISA table is frozen (Phase 1).
# Values are illustrative stubs until encode() is implemented.
OPCODES: dict[str, int] = {}


def encode_r(opcode: int, rd: int, funct3: int, rs1: int, rs2: int, funct7: int) -> int:
    """Pack an R-type instruction word."""
    return (
        (funct7 & 0x7F) << 25
        | (rs2 & 0x1F) << 20
        | (rs1 & 0x1F) << 15
        | (funct3 & 0x7) << 12
        | (rd & 0x1F) << 7
        | (opcode & 0x7F)
    )


def encode_instruction(mnemonic: str, operands: list[str], *, pc: int = 0) -> int:
    raise NotImplementedError("encode_instruction is not implemented yet")
