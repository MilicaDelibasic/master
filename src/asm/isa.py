"""RISC-V RV32I subset: instruction table and register names.

Single source of truth for which instructions the assembler supports and how
each one is encoded (format, opcode, funct3, funct7). Values follow the
RISC-V Unprivileged ISA specification, version 20191213, chapter 2.

Mnemonics and register names are case-insensitive; lookups normalize to
lowercase.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Format(Enum):
    """Instruction encoding formats (bit layouts) of RV32I."""

    R = "R"
    I = "I"
    S = "S"
    B = "B"
    U = "U"
    J = "J"


class Syntax(Enum):
    """Operand shape as written in assembly source."""

    RD_RS1_RS2 = "rd, rs1, rs2"  # add x3, x1, x2
    RD_RS1_IMM = "rd, rs1, imm"  # addi x1, x0, 5
    RD_RS1_SHAMT = "rd, rs1, shamt"  # slli x1, x1, 3
    RD_MEM = "rd, imm(rs1)"  # lw t1, 8(sp) / jalr ra, 0(t0)
    RS2_MEM = "rs2, imm(rs1)"  # sw t1, 8(sp)
    RS1_RS2_LABEL = "rs1, rs2, label"  # beq t0, t1, loop
    RD_IMM20 = "rd, imm20"  # lui t0, 0x12345
    RD_LABEL = "rd, label"  # jal ra, func

    @property
    def operand_count(self) -> int:
        return self.value.count(",") + 1


@dataclass(frozen=True, slots=True)
class InstructionSpec:
    mnemonic: str
    format: Format
    syntax: Syntax
    opcode: int  # bits [6:0]
    funct3: int | None = None  # bits [14:12]; None for U/J
    # bits [31:25] for R-type; for shift-immediates the same bits hold
    # imm[11:5] (0b0100000 selects srai over srli)
    funct7: int | None = None


# Major opcodes (spec table 24.1)
OP = 0b0110011
OP_IMM = 0b0010011
LOAD = 0b0000011
STORE = 0b0100011
BRANCH = 0b1100011
JALR = 0b1100111
JAL = 0b1101111
LUI = 0b0110111
AUIPC = 0b0010111


def _table(*specs: InstructionSpec) -> dict[str, InstructionSpec]:
    return {spec.mnemonic: spec for spec in specs}


_F, _S = Format, Syntax

INSTRUCTIONS: dict[str, InstructionSpec] = _table(
    # R-type: register-register arithmetic and logic
    InstructionSpec("add", _F.R, _S.RD_RS1_RS2, OP, 0b000, 0b0000000),
    InstructionSpec("sub", _F.R, _S.RD_RS1_RS2, OP, 0b000, 0b0100000),
    InstructionSpec("sll", _F.R, _S.RD_RS1_RS2, OP, 0b001, 0b0000000),
    InstructionSpec("slt", _F.R, _S.RD_RS1_RS2, OP, 0b010, 0b0000000),
    InstructionSpec("sltu", _F.R, _S.RD_RS1_RS2, OP, 0b011, 0b0000000),
    InstructionSpec("xor", _F.R, _S.RD_RS1_RS2, OP, 0b100, 0b0000000),
    InstructionSpec("srl", _F.R, _S.RD_RS1_RS2, OP, 0b101, 0b0000000),
    InstructionSpec("sra", _F.R, _S.RD_RS1_RS2, OP, 0b101, 0b0100000),
    InstructionSpec("or", _F.R, _S.RD_RS1_RS2, OP, 0b110, 0b0000000),
    InstructionSpec("and", _F.R, _S.RD_RS1_RS2, OP, 0b111, 0b0000000),
    # I-type: register-immediate arithmetic and logic
    InstructionSpec("addi", _F.I, _S.RD_RS1_IMM, OP_IMM, 0b000),
    InstructionSpec("slti", _F.I, _S.RD_RS1_IMM, OP_IMM, 0b010),
    InstructionSpec("sltiu", _F.I, _S.RD_RS1_IMM, OP_IMM, 0b011),
    InstructionSpec("xori", _F.I, _S.RD_RS1_IMM, OP_IMM, 0b100),
    InstructionSpec("ori", _F.I, _S.RD_RS1_IMM, OP_IMM, 0b110),
    InstructionSpec("andi", _F.I, _S.RD_RS1_IMM, OP_IMM, 0b111),
    # I-type: shifts by immediate (shamt in imm[4:0], funct7 in imm[11:5])
    InstructionSpec("slli", _F.I, _S.RD_RS1_SHAMT, OP_IMM, 0b001, 0b0000000),
    InstructionSpec("srli", _F.I, _S.RD_RS1_SHAMT, OP_IMM, 0b101, 0b0000000),
    InstructionSpec("srai", _F.I, _S.RD_RS1_SHAMT, OP_IMM, 0b101, 0b0100000),
    # I-type: loads
    InstructionSpec("lb", _F.I, _S.RD_MEM, LOAD, 0b000),
    InstructionSpec("lh", _F.I, _S.RD_MEM, LOAD, 0b001),
    InstructionSpec("lw", _F.I, _S.RD_MEM, LOAD, 0b010),
    InstructionSpec("lbu", _F.I, _S.RD_MEM, LOAD, 0b100),
    InstructionSpec("lhu", _F.I, _S.RD_MEM, LOAD, 0b101),
    # I-type: indirect jump
    InstructionSpec("jalr", _F.I, _S.RD_MEM, JALR, 0b000),
    # S-type: stores
    InstructionSpec("sb", _F.S, _S.RS2_MEM, STORE, 0b000),
    InstructionSpec("sh", _F.S, _S.RS2_MEM, STORE, 0b001),
    InstructionSpec("sw", _F.S, _S.RS2_MEM, STORE, 0b010),
    # B-type: conditional branches (PC-relative)
    InstructionSpec("beq", _F.B, _S.RS1_RS2_LABEL, BRANCH, 0b000),
    InstructionSpec("bne", _F.B, _S.RS1_RS2_LABEL, BRANCH, 0b001),
    InstructionSpec("blt", _F.B, _S.RS1_RS2_LABEL, BRANCH, 0b100),
    InstructionSpec("bge", _F.B, _S.RS1_RS2_LABEL, BRANCH, 0b101),
    InstructionSpec("bltu", _F.B, _S.RS1_RS2_LABEL, BRANCH, 0b110),
    InstructionSpec("bgeu", _F.B, _S.RS1_RS2_LABEL, BRANCH, 0b111),
    # U-type: upper immediates
    InstructionSpec("lui", _F.U, _S.RD_IMM20, LUI),
    InstructionSpec("auipc", _F.U, _S.RD_IMM20, AUIPC),
    # J-type: direct jump (PC-relative)
    InstructionSpec("jal", _F.J, _S.RD_LABEL, JAL),
)


def lookup_instruction(mnemonic: str) -> InstructionSpec | None:
    """Return the spec for a real (non-pseudo) instruction, or None."""
    return INSTRUCTIONS.get(mnemonic.lower())


# -- registers ----------------------------------------------------------

# ABI names in register order x0..x31 (calling convention, spec chapter 25)
ABI_NAMES: tuple[str, ...] = (
    "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
    "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
    "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
    "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6",
)

REGISTERS: dict[str, int] = {
    **{f"x{n}": n for n in range(32)},
    **{name: n for n, name in enumerate(ABI_NAMES)},
    "fp": 8,  # frame pointer, alias of s0
}


def register_number(name: str) -> int | None:
    """Map a register name (x5, t0, fp, ...) to 0..31, or None if unknown."""
    return REGISTERS.get(name.lower())
