"""Encode RISC-V RV32I instructions into 32-bit machine words.

Two layers:

- ``encode_r/i/s/b/u/j`` pack already-resolved fields into a word for one
  format (spec chapter 2.2–2.3) and check that immediates fit;
- ``encode`` takes an ``InstructionSpec`` from ``asm.isa`` plus operand
  values and picks the right packer.

Immediates are plain Python ints (negative for negative values). Branch and
jump targets are passed as PC-relative byte offsets (``target - pc``); the
assembler's second pass computes them.

Out-of-range immediates raise ``SemanticError`` (with the caller's source
location); out-of-range register numbers raise ``ValueError`` because the
register map in ``asm.isa`` can only produce 0..31.
"""

from __future__ import annotations

from asm.errors import SemanticError, SourceLocation
from asm.isa import Format, InstructionSpec, Syntax

# Opcode/funct tables live in asm.isa (single source of truth).


# -- range checks ---------------------------------------------------------


def _check_reg(*regs: int) -> None:
    for reg in regs:
        if not 0 <= reg < 32:
            raise ValueError(f"register number out of range: {reg}")


def _check_signed(value: int, bits: int, what: str, location: SourceLocation | None) -> None:
    low, high = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    if not low <= value <= high:
        raise SemanticError(f"{what} {value} out of range ({low}..{high})", location=location)


def _check_even(value: int, what: str, location: SourceLocation | None) -> None:
    if value % 2:
        raise SemanticError(f"{what} {value} is not a multiple of 2", location=location)


# -- per-format packers -----------------------------------------------------


def encode_r(opcode: int, rd: int, funct3: int, rs1: int, rs2: int, funct7: int) -> int:
    """Pack an R-type instruction word."""
    _check_reg(rd, rs1, rs2)
    return (
        (funct7 & 0x7F) << 25
        | (rs2 & 0x1F) << 20
        | (rs1 & 0x1F) << 15
        | (funct3 & 0x7) << 12
        | (rd & 0x1F) << 7
        | (opcode & 0x7F)
    )


def encode_i(
    opcode: int, rd: int, funct3: int, rs1: int, imm: int,
    *, location: SourceLocation | None = None,
) -> int:
    """Pack an I-type word; imm is a signed 12-bit value (-2048..2047)."""
    _check_reg(rd, rs1)
    _check_signed(imm, 12, "immediate", location)
    return (
        (imm & 0xFFF) << 20
        | rs1 << 15
        | (funct3 & 0x7) << 12
        | rd << 7
        | (opcode & 0x7F)
    )


def encode_s(
    opcode: int, funct3: int, rs1: int, rs2: int, imm: int,
    *, location: SourceLocation | None = None,
) -> int:
    """Pack an S-type word; the 12-bit offset is split into imm[11:5] and imm[4:0]."""
    _check_reg(rs1, rs2)
    _check_signed(imm, 12, "offset", location)
    imm &= 0xFFF
    return (
        (imm >> 5) << 25
        | rs2 << 20
        | rs1 << 15
        | (funct3 & 0x7) << 12
        | (imm & 0x1F) << 7
        | (opcode & 0x7F)
    )


def encode_b(
    opcode: int, funct3: int, rs1: int, rs2: int, offset: int,
    *, location: SourceLocation | None = None,
) -> int:
    """Pack a B-type word; offset is PC-relative, even, -4096..4094.

    Bit layout: imm[12] → 31, imm[10:5] → 30:25, imm[4:1] → 11:8, imm[11] → 7.
    imm[0] is not stored (always 0).
    """
    _check_reg(rs1, rs2)
    _check_signed(offset, 13, "branch offset", location)
    _check_even(offset, "branch offset", location)
    imm = offset & 0x1FFF
    return (
        ((imm >> 12) & 0x1) << 31
        | ((imm >> 5) & 0x3F) << 25
        | rs2 << 20
        | rs1 << 15
        | (funct3 & 0x7) << 12
        | ((imm >> 1) & 0xF) << 8
        | ((imm >> 11) & 0x1) << 7
        | (opcode & 0x7F)
    )


def encode_u(
    opcode: int, rd: int, imm20: int,
    *, location: SourceLocation | None = None,
) -> int:
    """Pack a U-type word; imm20 is the upper 20 bits (0..0xFFFFF), as written in lui/auipc."""
    _check_reg(rd)
    if not 0 <= imm20 <= 0xFFFFF:
        raise SemanticError(
            f"upper immediate {imm20} out of range (0..{0xFFFFF})", location=location
        )
    return imm20 << 12 | rd << 7 | (opcode & 0x7F)


def encode_j(
    opcode: int, rd: int, offset: int,
    *, location: SourceLocation | None = None,
) -> int:
    """Pack a J-type word; offset is PC-relative, even, -1048576..1048574.

    Bit layout: imm[20] → 31, imm[10:1] → 30:21, imm[11] → 20, imm[19:12] → 19:12.
    """
    _check_reg(rd)
    _check_signed(offset, 21, "jump offset", location)
    _check_even(offset, "jump offset", location)
    imm = offset & 0x1FFFFF
    return (
        ((imm >> 20) & 0x1) << 31
        | ((imm >> 1) & 0x3FF) << 21
        | ((imm >> 11) & 0x1) << 20
        | ((imm >> 12) & 0xFF) << 12
        | rd << 7
        | (opcode & 0x7F)
    )


# -- spec-driven entry point ------------------------------------------------


def encode(
    spec: InstructionSpec,
    *,
    rd: int = 0,
    rs1: int = 0,
    rs2: int = 0,
    imm: int = 0,
    location: SourceLocation | None = None,
) -> int:
    """Encode one real instruction from its table entry and resolved operands.

    ``imm`` means: the immediate (I/S), the shift amount (shifts), imm20
    (U), or the PC-relative byte offset (B/J). Unused fields are ignored.
    """
    op, f3, f7 = spec.opcode, spec.funct3, spec.funct7
    match spec.format:
        case Format.R:
            return encode_r(op, rd, f3, rs1, rs2, f7)
        case Format.I if spec.syntax is Syntax.RD_RS1_SHAMT:
            if not 0 <= imm <= 31:
                raise SemanticError(f"shift amount {imm} out of range (0..31)", location=location)
            # funct7 occupies imm[11:5], shamt imm[4:0]; at most 0x41F, so it
            # always fits the signed 12-bit field
            return encode_i(op, rd, f3, rs1, f7 << 5 | imm)
        case Format.I:
            return encode_i(op, rd, f3, rs1, imm, location=location)
        case Format.S:
            return encode_s(op, f3, rs1, rs2, imm, location=location)
        case Format.B:
            return encode_b(op, f3, rs1, rs2, imm, location=location)
        case Format.U:
            return encode_u(op, rd, imm, location=location)
        case Format.J:
            return encode_j(op, rd, imm, location=location)
    raise AssertionError(f"unhandled format {spec.format}")


# -- 32-bit constants (li / la) ----------------------------------------------


def split_hi_lo(value: int, *, location: SourceLocation | None = None) -> tuple[int, int]:
    """Split a 32-bit value into (hi20, lo12) so that (hi20 << 12) + lo12 == value (mod 2**32).

    lo12 is signed (-2048..2047) because addi sign-extends it, so hi20 is
    rounded up when bit 11 is set: hi20 = (value + 0x800) >> 12.
    Used for ``lui rd, hi20`` + ``addi rd, rd, lo12`` and ``auipc`` + ``addi``.
    """
    if not -(1 << 31) <= value <= 0xFFFFFFFF:
        raise SemanticError(f"value {value} does not fit in 32 bits", location=location)
    hi = (value + 0x800) >> 12
    lo = value - (hi << 12)
    return hi & 0xFFFFF, lo
